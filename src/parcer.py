from abc import ABC, abstractmethod
from pathlib import Path
import logging
import easyocr
import whisper

## for pics
from PIL import Image
import pytesseract

# for structured data
import json
import csv
import pandas as pd
import logging
from pathlib import Path



class Parser(ABC):
    def __init__(self):
        pass
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