from abc import ABC, abstractmethod
from pathlib import Path
import logging
import easyocr
import whisper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Parser(ABC):
    def __init__(self):
        logger.info("Загрузка моделей... Это может занять время при первом запуске")
        self.ocr_reader = None
        self.whisper_model = None
    def _get_ocr_reader(self):
        """Ленивая загрузка OCR модели"""
        if self.ocr_reader is None:
            logger.info("Загрузка EasyOCR модели...")
            self.ocr_reader = easyocr.Reader(['ru', 'en'])
        return self.ocr_reader
    
    def _get_whisper_model(self):
        """Ленивая загрузка Whisper модели"""
        if self.whisper_model is None:
            logger.info("Загрузка Whisper модели...")
            self.whisper_model = whisper.load_model("base")
        return self.whisper_model
    @abstractmethod
    def parse(self, data_path: Path)->dict:
        pass

class StructureData(Parser):
    pass

class Documents(Parser):
    pass

class WebContent(Parser):
    pass

class Images(Parser):
    pass

class Videos(Parser):
    pass
