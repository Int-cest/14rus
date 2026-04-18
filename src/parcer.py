from abc import ABC, abstractmethod
from pathlib import Path
import logging


## for pics
from PIL import Image
import cv2
import easyocr

# for structured data
import json
import csv
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Parser(ABC):
    def __init__(self):
        logger.info("Загрузка моделей... Это может занять время при первом запуске")
        self.ocr_reader = None

    def _get_ocr_reader(self):
        """Ленивая загрузка OCR модели"""
        if self.ocr_reader is None:
            logger.info("Загрузка EasyOCR модели...")
            self.ocr_reader = easyocr.Reader(['ru', 'en'])
        return self.ocr_reader
    
    @abstractmethod
    def parse(self, data_path: Path)->str:
        pass

class StructureData(Parser):
    def __init__(self):
        super().__init__()

    def _flatten_to_text(self, data) -> str:
        words = []
        if isinstance(data, dict):
            for key, value in data.items():
                words.append(str(key))
                words.append(self._flatten_to_text(value))
        elif isinstance(data, (list, tuple)):
            for item in data:
                words.append(self._flatten_to_text(item))
        else:
            words.append(str(data))
        return " ".join(filter(None, words))

    def parse(self, data_path: Path) -> dict:
        suffix = data_path.suffix.lower()
        result = {
            "file_name": data_path.name,
            "type": "structured_data",
            "content": ""
        }

        try:
            raw_data = None
            if suffix == '.json':
                with open(data_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)

            elif suffix == '.csv':
                with open(data_path, 'r', encoding='utf-8') as f:
                    raw_data = list(csv.DictReader(f))

            elif suffix == '.parquet':
                df = pd.read_parquet(data_path)
                raw_data = df.to_dict(orient='records')
            
            if raw_data is not None:
                result["content"] = self._flatten_to_text(raw_data)
            else:
                logging.warning(f"Unsupported format: {suffix}")

        except Exception as e:
            logging.error(f"Error parsing {data_path}: {e}")
            result["content"] = f"Error: {str(e)}"

        return result

class Documents(Parser):
    pass

class WebContent(Parser):
    pass

class Images(Parser):
    def __init__(self, use_ocr: bool = True):
        super().__init__()
        self.use_ocr = use_ocr

    def parse(self, data_path: Path) -> str:
        if not self.use_ocr:
            return ""

        try:
            reader = self._get_ocr_reader()
            result = reader.readtext(str(data_path), detail=0)

            return " ".join(result).strip()

        except Exception as e:
            logger.info(f"[Images Parser] Error processing {data_path}: {e}")
            return ""

class Videos(Parser):
    def __init__(self, use_ocr=True, frame_interval=30, max_frames=200):
        super().__init__()
        self.use_ocr = use_ocr
        self.frame_interval = frame_interval
        self.max_frames = max_frames

    def parse(self, file_path: Path) -> str:
        if not self.use_ocr:
            return ""

        texts = []

        try:
            reader = self._get_ocr_reader()
            cap = cv2.VideoCapture(str(file_path))

            if not cap.isOpened():
                logger.info(f"[Videos Parser] Cannot open {file_path}")
                return ""

            frame_id = 0
            processed = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_id % self.frame_interval == 0:
                    result = reader.readtext(frame, detail=0)

                    if result:
                        text = " ".join(result).strip()
                        if len(text) > 5:
                            texts.append(text)

                    processed += 1
                    if processed >= self.max_frames:
                        break

                frame_id += 1

            cap.release()

            return "\n".join(texts)

        except Exception as e:
            logger.info(f"[Videos Parser] Error processing {file_path}: {e}")
            return ""