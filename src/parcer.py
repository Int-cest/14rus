from abc import ABC, abstractmethod
from pathlib import Path
import logging


## for pics
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
        self.ocr_reader = None
     
    def _get_ocr_reader(self):
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
    def parse(self, data_path: Path) -> dict:
        return {"path": str(data_path), "content": "Doc parser not implemented", "type": "doc"}

class WebContent(Parser):
    def parse(self, data_path: Path) -> dict:
        return {"path": str(data_path), "content": "Web parser not implemented", "type": "web"}


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

    def parse(self, data_path: Path) -> str:
        if not self.use_ocr:
            return ""

        texts = []

        try:
            reader = self._get_ocr_reader()
            cap = cv2.VideoCapture(str(data_path))

            if not cap.isOpened():
                logger.info(f"[Videos Parser] Cannot open {data_path}")
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
            logger.info(f"[Videos Parser] Error processing {data_path}: {e}")
            return ""
        
class ParserFactory:
    def __init__(self):
        self.extension_map = {
            '.csv': 'structured', '.json': 'structured', '.parquet': 'structured',
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image',
            '.mp4': 'video', '.pdf': 'document', '.html': 'web'
        }
        self._parsers_cache = {}

    def _get_parser(self, file_type: str):
        if file_type not in self._parsers_cache:
            if file_type == 'structured': self._parsers_cache[file_type] = StructureData()
            elif file_type == 'image': self._parsers_cache[file_type] = Images()
            elif file_type == 'video': self._parsers_cache[file_type] = Videos()
            elif file_type == 'document': self._parsers_cache[file_type] = Documents()
            elif file_type == 'web': self._parsers_cache[file_type] = WebContent()
        return self._parsers_cache.get(file_type)

    def process_file(self, file_path: Path):
        file_type = self.extension_map.get(file_path.suffix.lower())
        if not file_type: return None
        parser = self._get_parser(file_type)
        return parser.parse(file_path)

    def scan_directory(self, root_path: str):
        root = Path(root_path)
        results = []
        for file in root.rglob('*'):
            if file.is_file():
                res = self.process_file(file)
                if res: results.append(res)
        return results
