from abc import ABC, abstractmethod
from pathlib import Path
import logging
import easyocr
import whisper


class Parser(ABC):
    def __init__(self):
        self.ocr_reader = easyocr.Reader(['ru', 'en']) # Загружает модели ~1ГБ
        self.whisper_model = whisper.load_model("base") # Загружает модели ~1ГБ
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

