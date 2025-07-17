from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .core.config import settings
from .routes import predict
from .utils.predict_fn import get_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    import os
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

    logger.info("Starting up Shakespearean Poem Generator API...")
    try:
        get_model()
        logger.info("Model initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model: {str(e)}")
    yield
    logger.info("Shutting down...")

def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Generate beautiful Shakespearean poetry from your prompts",
        version=settings.VERSION,
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(predict.router, prefix=settings.API_V1_STR)

    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": settings.VERSION,
            "endpoints": {
                "generate_stream": f"{settings.API_V1_STR}/generate-poem",
                "generate_sync": f"{settings.API_V1_STR}/generate-poem-sync",
                "health": f"{settings.API_V1_STR}/health",
                "docs": "/docs"
            }
        }

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",  # assumes main.py is inside app/ folder
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
