import pickle
import asyncio
import logging
import numpy as np
import os
from typing import AsyncGenerator, Optional
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from ..core.config import settings

logger = logging.getLogger(__name__)

class ShakespeareanModelWrapper:
    def __init__(self):
        self.model_path = settings.MODEL_PATH
        self.tokenizer_path = settings.TOKENIZER_PATH
        self.model = None
        self.tokenizer = None
        self.max_seq_len = None
        self.load_model_and_tokenizer()

    def load_model_and_tokenizer(self):
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model not found at {self.model_path}")
            if not os.path.exists(self.tokenizer_path):
                raise FileNotFoundError(f"Tokenizer not found at {self.tokenizer_path}")

            self.model = load_model(self.model_path)
            self.tokenizer = pickle.load(open(self.tokenizer_path, 'rb'))
            self.max_seq_len = self.model.input_shape[1]

            logger.info("Model and tokenizer loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model or tokenizer: {str(e)}")
            raise

    def generate_poem(self, prompt: str, num_words: int = 20, temperature: float = 0.7) -> str:
        line = prompt.strip()
        for _ in range(num_words):
            token_list = self.tokenizer.texts_to_sequences([line])[0]
            token_list = pad_sequences([token_list], maxlen=self.max_seq_len - 1, padding='pre')
            predicted = self.model.predict(token_list, verbose=0)
            
            # Apply temperature scaling (softmax sampling)
            preds = np.asarray(predicted).astype("float64")[0]
            preds = np.log(preds + 1e-7) / temperature
            exp_preds = np.exp(preds)
            preds = exp_preds / np.sum(exp_preds)
            probas = np.random.multinomial(1, preds, 1)
            predicted_index = np.argmax(probas)

            next_word = None
            for word, index in self.tokenizer.word_index.items():
                if index == predicted_index:
                    next_word = word
                    break
            if not next_word:
                break

            line += " " + next_word
        return line

    async def generate_stream(self, prompt: str, max_words: int = 20, temperature: float = 0.7) -> AsyncGenerator[str, None]:
        try:
            full_poem = await asyncio.to_thread(self.generate_poem, prompt, max_words, temperature)
            words = full_poem.split()
            for i, word in enumerate(words):
                yield f"{' ' if i != 0 else ''}{word}"
                if word.endswith(('.', '!', '?', ';', ':', '\n')):
                    await asyncio.sleep(settings.STREAM_DELAY * 4)
                elif word.endswith(','):
                    await asyncio.sleep(settings.STREAM_DELAY * 2)
                else:
                    await asyncio.sleep(settings.STREAM_DELAY)
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield f"[Error] {str(e)}"

# Singleton model instance
model_instance: Optional[ShakespeareanModelWrapper] = None

def get_model() -> ShakespeareanModelWrapper:
    global model_instance
    if model_instance is None:
        model_instance = ShakespeareanModelWrapper()
    return model_instance
