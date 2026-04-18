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

# for docs
import win32com.client
import fitz
from docx import Document as DocxDocument

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
        content = ""
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
                content = self._flatten_to_text(raw_data)
        except Exception as e:
            content = f"Error: {e}"
        return {"path": str(data_path), "content": content}

class Documents(Parser):
    def _read_doc_via_word(self, file_path: Path) -> str:
        """Чтение .doc через COM-объект Word (только для Windows)"""
        word = None
        doc = None
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            
            abs_path = str(file_path.absolute())
            
            doc = word.Documents.Open(abs_path, ReadOnly=True)
            text = doc.Content.Text
            return text
        except Exception as e:
            logging.error(f"Word COM error: {e}")
            return ""
        finally:
            if doc:
                doc.Close(False)
            if word:
                word.Quit()

    def parse(self, data_path: Path) -> dict:
        suffix = data_path.suffix.lower()
        content = ""
        try:
            if suffix == '.pdf':
                with fitz.open(data_path) as doc:
                    content = " ".join([page.get_text() for page in doc])
            
            elif suffix == '.docx':
                doc = DocxDocument(data_path)
                content = " ".join([p.text for p in doc.paragraphs])
            
            elif suffix == '.doc':
                content = self._read_doc_via_word(data_path)
            
            elif suffix in ['.xls', '.xlsx']:
                df = pd.read_excel(data_path)
                content = df.to_string(index=False, header=False)
            
            elif suffix in ['.md', '.txt']:
                with open(data_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            elif suffix == '.rtf':
                content = self._read_doc_via_word(data_path)

            content = " ".join(content.split())
        except Exception as e:
            content = f"Error: {e}"
            
        return {"path": str(data_path), "content": content}

class WebContent(Parser):
    def parse(self, data_path: Path) -> dict:
        return {"path": str(data_path), "content": "Web parser not implemented", "type": "web"}


class Images(Parser):
    def parse(self, file_path: Path):
        try:
            reader = self._get_ocr_reader()
            text = reader.readtext(str(file_path), detail=0)

            return {
                'path': str(file_path),
                'content': "".join(text).strip()
            }

        except Exception as e:
            logger.info(f"[Images] {e}")
            return {file_path: ""}
        
class Videos(Parser):
    def __init__(self, frame_interval=30, max_frames=200):
        super().__init__()
        self.frame_interval = frame_interval
        self.max_frames = max_frames

    def parse(self, file_path: Path) -> dict[Path, str]:
        try:
            reader = self._get_ocr_reader()
            cap = cv2.VideoCapture(str(file_path))

            texts = []
            i = 0
            used = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if i % self.frame_interval == 0:
                    result = reader.readtext(frame, detail=0)

                    if result:
                        texts.append(" ".join(result))

                    used += 1
                    if used >= self.max_frames:
                        break

                i += 1

            cap.release()

            return {
                'path': str(file_path),
                'content': "\n".join(texts).strip()
            }

        except Exception as e:
            logger.info(f"[Videos] {e}")
            return {'path': str(file_path), "content": ''}
        
class ParserFactory:
    def __init__(self):
        self.extension_map = {
            # Structured Data (Таблицы и базы)
            '.csv': 'structured', 
            '.json': 'structured', 
            '.parquet': 'structured',
            '.xls': 'document',    # Excel обычно удобнее обрабатывать в Documents через pandas
            '.xlsx': 'document',

            # Images (Картинки с OCR)
            '.jpg': 'image', 
            '.jpeg': 'image', 
            '.png': 'image', 
            '.tif': 'image', 
            '.tiff': 'image', 
            '.gif': 'image',

            # Documents (Текстовые форматы)
            '.pdf': 'document', 
            '.docx': 'document', 
            '.doc': 'document', 
            '.rtf': 'document', 
            '.txt': 'document', 
            '.md': 'document',

            # Video (Раскадровка + OCR)
            '.mp4': 'video',

            # Web (HTML парсинг)
            '.html': 'web'
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
