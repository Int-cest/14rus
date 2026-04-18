from abc import ABC, abstractmethod
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import re
from html import unescape


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

from config import (
    EXTENSION_MAP,
    LOG_DATE_FORMAT,
    LOG_DIR,
    LOG_ERROR_FILE,
    LOG_FORMAT,
    LOG_INFO_FILE,
    LOG_LEVEL,
    OCR_LANGUAGES,
    PATH_DATA,
    VIDEO_FRAME_INTERVAL,
    VIDEO_MAX_FRAMES,
)

logger = logging.getLogger(__name__)


class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: int):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


def setup_logging():
    if logger.handlers:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    info_handler = RotatingFileHandler(LOG_INFO_FILE, maxBytes=5_000_000, backupCount=3, encoding='utf-8')
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(MaxLevelFilter(logging.WARNING))
    info_handler.setFormatter(formatter)

    error_handler = RotatingFileHandler(LOG_ERROR_FILE, maxBytes=5_000_000, backupCount=3, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)

class Parser(ABC):
    _ocr_reader = None

    def _get_ocr_reader(self):
        if Parser._ocr_reader is None:
            logger.info("Загрузка EasyOCR модели...")
            Parser._ocr_reader = easyocr.Reader(list(OCR_LANGUAGES))
        return Parser._ocr_reader
   
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
        logger.info("[StructureData] Старт парсинга %s", data_path)
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
            logger.warning("[StructureData] Ошибка парсинга %s: %s", data_path, e)
            content = f"Error: {e}"
        logger.info("[StructureData] Завершено %s | chars=%s", data_path, len(content))
        return {"path": str(data_path), "content": content}

class Documents(Parser):
    def _read_doc_via_word(self, file_path: Path) -> str:
        """Чтение .doc через COM-объект Word (только для Windows)"""
        word = None
        doc = None
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            logger.info("[Documents] Чтение через Word COM: %s", file_path)
            
            abs_path = str(file_path.absolute())
            
            doc = word.Documents.Open(abs_path, ReadOnly=True)
            text = doc.Content.Text
            return text
        except Exception as e:
            logger.error(f"Word COM error: {e}")
            return ""
        finally:
            if doc:
                doc.Close(False)
            if word:
                word.Quit()

    def parse(self, data_path: Path) -> dict:
        suffix = data_path.suffix.lower()
        content = ""
        logger.info("[Documents] Старт парсинга %s", data_path)
        try:
            if suffix == '.pdf':
                with fitz.open(data_path) as doc:
                    content = " ".join(page.get_text() for page in doc)
            
            elif suffix == '.docx':
                doc = DocxDocument(data_path)
                content = " ".join(p.text for p in doc.paragraphs)
            
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
            logger.warning("[Documents] Ошибка парсинга %s: %s", data_path, e)
            content = f"Error: {e}"
        logger.info("[Documents] Завершено %s | chars=%s", data_path, len(content))
            
        return {"path": str(data_path), "content": content}

class WebContent(Parser):
    def parse(self, data_path: Path) -> dict:
        logger.info("[WebContent] Старт парсинга %s", data_path)
        content = ""
        try:
            with open(data_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_text = f.read()

            html_text = re.sub(r'(?is)<(script|style).*?>.*?</\1>', ' ', html_text)
            content = re.sub(r'(?s)<[^>]+>', ' ', html_text)
            content = unescape(content)
            content = " ".join(content.split())
        except Exception as e:
            logger.warning("[WebContent] Ошибка парсинга %s: %s", data_path, e)
            content = f"Error: {e}"

        logger.info("[WebContent] Завершено %s | chars=%s", data_path, len(content))
        return {"path": str(data_path), "content": content, "type": "web"}


class Images(Parser):
    def parse(self, file_path: Path):
        logger.info("[Images] Старт OCR %s", file_path)
        try:
            reader = self._get_ocr_reader()
            text = reader.readtext(str(file_path), detail=0)

            result = {
                'path': str(file_path),
                'content': "".join(text).strip()
            }
            logger.info("[Images] Завершено %s | chars=%s", file_path, len(result['content']))
            return result

        except Exception as e:
            logger.warning(f"[Images] Ошибка OCR {file_path}: {e}")
            return {'path': str(file_path), 'content': ''}
        
class Videos(Parser):
    def __init__(self, frame_interval=VIDEO_FRAME_INTERVAL, max_frames=VIDEO_MAX_FRAMES):
        self.frame_interval = frame_interval
        self.max_frames = max_frames

    def parse(self, file_path: Path) -> dict[Path, str]:
        logger.info("[Videos] Старт OCR по кадрам %s", file_path)
        cap = None
        try:
            reader = self._get_ocr_reader()
            cap = cv2.VideoCapture(str(file_path))
            if not cap.isOpened():
                return {'path': str(file_path), "content": ''}

            texts = []
            used = 0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            step = self.frame_interval

            if total_frames > 0:
                step = max(self.frame_interval, max(1, total_frames // max(1, self.max_frames)))

            frame_indices = list(range(0, total_frames, step))[:self.max_frames] if total_frames > 0 else []

            if frame_indices:
                for frame_index in frame_indices:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                    ret, frame = cap.read()
                    if not ret:
                        continue

                    result = reader.readtext(frame, detail=0)
                    if result:
                        texts.append(" ".join(result))

                    used += 1
            else:
                i = 0
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

            result = {
                'path': str(file_path),
                'content': "\n".join(texts).strip()
            }
            logger.info("[Videos] Завершено %s | sampled_frames=%s | chars=%s", file_path, used, len(result['content']))
            return result

        except Exception as e:
            logger.warning(f"[Videos] Ошибка OCR {file_path}: {e}")
            return {'path': str(file_path), "content": ''}
        finally:
            if cap is not None:
                cap.release()
        
class ParserFactory:
    def __init__(self):
        self.extension_map = EXTENSION_MAP.copy()
        self._parsers_cache = {}
        self.base_path = Path(PATH_DATA)
        logger.info("[ParserFactory] Инициализирован. Поддерживаемых расширений: %s", len(self.extension_map))

    def _get_parser(self, file_type: str):
        if file_type not in self._parsers_cache:
            logger.info("[ParserFactory] Создание парсера для типа: %s", file_type)
            if file_type == 'structured': self._parsers_cache[file_type] = StructureData()
            elif file_type == 'image': self._parsers_cache[file_type] = Images()
            elif file_type == 'video': self._parsers_cache[file_type] = Videos()
            elif file_type == 'document': self._parsers_cache[file_type] = Documents()
            elif file_type == 'web': self._parsers_cache[file_type] = WebContent()
        return self._parsers_cache.get(file_type)

    def process_file(self, file_path: Path):
        file_type = self.extension_map.get(file_path.suffix.lower())
        if not file_type:
            logger.debug("[ParserFactory] Пропуск неподдерживаемого файла %s", file_path)
            return None
        parser = self._get_parser(file_type)
        logger.info("[ParserFactory] %s -> %s", file_path, file_type)
        result = parser.parse(file_path)
        if result and "path" in result:
            try:
                result["path"] = str(Path(result["path"]).resolve().relative_to(self.base_path.resolve()))
            except Exception:
                result["path"] = str(file_path.name)
        return result

    def scan_directory(self, root_path: str):
        root = Path(root_path)
        self.base_path = root
        logger.info("[ParserFactory] Старт сканирования директории: %s", root)
        results = []
        total_files = 0
        parsed_files = 0
        supported_extensions = set(self.extension_map.keys())
        for file in root.rglob('*'):
            if file.is_file():
                total_files += 1
                if file.suffix.lower() not in supported_extensions:
                    continue
                res = self.process_file(file)
                if res:
                    parsed_files += 1
                    results.append(res)
        logger.info("[ParserFactory] Сканирование завершено: total_files=%s, parsed_files=%s", total_files, parsed_files)
        return results


setup_logging()
