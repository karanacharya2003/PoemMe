from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging
import asyncio
from typing import Optional, AsyncGenerator
import uuid

from ..utils.predict_fn import get_model
from ..core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/response models
class PoemRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    max_length: Optional[int] = Field(default=200, ge=20, le=1000)
    temperature: Optional[float] = Field(default=0.7, ge=0.1, le=1.5)

class PoemResponse(BaseModel):
    text: str
    done: bool
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    model_status: str
    active_streams: int

active_streams = {}

@router.post("/generate-poem")
async def generate_poem_stream(request: PoemRequest, background_tasks: BackgroundTasks):
    try:
        model = get_model()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model not available: {str(e)}")

    stream_id = str(uuid.uuid4())

    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            active_streams[stream_id] = {"status": "active", "prompt": request.prompt}
            logger.info(f"Generating stream for: {request.prompt[:50]}")

            async for chunk in model.generate_stream(request.prompt, max_words=request.max_length, temperature=request.temperature):
                if active_streams.get(stream_id, {}).get("status") == "cancelled":
                    logger.info(f"Stream {stream_id} cancelled.")
                    break
                response = PoemResponse(text=chunk, done=False)
                yield f"data: {response.json()}\n\n"

            yield f"data: {PoemResponse(text='', done=True).json()}\n\n"
            logger.info(f"Stream {stream_id} completed.")

        except Exception as e:
            logger.error(f"Error in stream {stream_id}: {str(e)}")
            yield f"data: {PoemResponse(text='', done=True, error=str(e)).json()}\n\n"

        finally:
            active_streams.pop(stream_id, None)

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"X-Stream-ID": stream_id}
    )

@router.post("/generate-poem-sync", response_model=PoemResponse)
async def generate_poem_sync(request: PoemRequest):
    try:
        model = get_model()
        poem = await asyncio.to_thread(model.generate_poem, request.prompt, request.max_length, request.temperature)
        return PoemResponse(text=poem, done=True)
    except Exception as e:
        logger.error(f"Sync generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel-stream/{stream_id}")
async def cancel_stream(stream_id: str):
    if stream_id in active_streams:
        active_streams[stream_id]["status"] = "cancelled"
        return {"message": f"Stream {stream_id} cancelled"}
    raise HTTPException(status_code=404, detail="Stream not found")

@router.get("/active-streams")
async def get_active_streams():
    return {"active_streams": list(active_streams.keys()), "count": len(active_streams)}

@router.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        model = get_model()
        model_status = "loaded" if model.model else "not loaded"
    except Exception:
        model_status = "error"

    return HealthResponse(
        status="healthy",
        model_status=model_status,
        active_streams=len(active_streams)
    )
