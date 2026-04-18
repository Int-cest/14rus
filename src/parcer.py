from abc import ABC, abstractmethod
from pathlib import Path
import logging
import easyocr
import whisper

## for pics
from PIL import Image
import pytesseract



class Parser(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def parse(self, data_path: Path)->str:
        pass

class StructureData(Parser):
    pass

class Documents(Parser):
    pass

class WebContent(Parser):
    pass

class Images(Parser):
    def __init__(self, use_ocr: bool = True, lang: str = "rus+eng"):
        self.use_ocr = use_ocr
        self.lang = lang

    def parse(self, data_path: Path)->str:
        pass

class Videos(Parser):
    self._get_ocr_reader()

    def parse(self, data_path:Path)->str:
        try:
            ## open image
            with Image.open(data_path) as img:
                img = img.convert("RGB")

                if not self.use_ocr:
                    return ""

                # OCR
                text = pytesseract.image_to_string(img, lang=self.lang)

                return text.strip()

        except Exception as e:
            logger.info(f"[Images Parser] Error processing {data_path}: {e}")
            return ""