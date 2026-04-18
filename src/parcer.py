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
    pass

class WebContent(Parser):
    pass

class Images(Parser):
    def parse(self, file_path: Path) -> dict[Path, str]:
        try:
            reader = self._get_ocr_reader()
            text = reader.readtext(str(file_path), detail=0)

            return {
                file_path: " ".join(text).strip()
            }

        except Exception as e:
            logger.info(f"[Images] {e}")
            return {file_path: ""}
        
class Videos(Parser):
    def __init__(self, frame_interval=30, max_frames=200):
        super().__init__()
        self.frame_interval = frame_interval
        self.max_frames = max_frames

    def parse(self, data_path: Path) -> dict[Path, str]:
        try:
            reader = self._get_ocr_reader()
            cap = cv2.VideoCapture(str(data_path))

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
                data_path: "\n".join(texts).strip()
            }

        except Exception as e:
            logger.info(f"[Videos] {e}")
            return {data_path: ""}
        
class ParserFactory:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        # Маппинг расширений к классам-парсерам
        self.extension_map = {
            # Structured
            '.csv': 'structured', '.json': 'structured', '.parquet': 'structured',
            # Images
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image', '.tif': 'image', '.tiff': 'image',
            # Documents
            '.pdf': 'document', '.doc': 'document', '.docx': 'document', '.rtf': 'document', '.txt': 'document', '.md': 'document',
            # Video
            '.mp4': 'video',
            # Web
            '.html': 'web'
        }
        # Кэш созданных экземпляров парсеров
        self._parsers_cache = {}

    def _get_parser(self, file_type: str):
        """Фабричный метод для получения парсера (Lazy Loading)"""
        if file_type not in self._parsers_cache:
            if file_type == 'structured':
                self._parsers_cache[file_type] = StructureData()
            elif file_type == 'image':
                self._parsers_cache[file_type] = Images(use_ocr=True)
            elif file_type == 'document':
                self._parsers_cache[file_type] = Documents()
            elif file_type == 'video':
                self._parsers_cache[file_type] = Videos(use_ocr=True)
            elif file_type == 'web':
                self._parsers_cache[file_type] = WebContent()
        return self._parsers_cache.get(file_type)

    def process_file(self, file_path: Path):
        """
        Диспетчер: определяет тип файла и пробрасывает задачу в нужный парсер.
        Парсеры сами возвращают dict{'path': ..., 'content': ...}
        """
        suffix = file_path.suffix.lower()
        file_type = self.extension_map.get(suffix)
        
        # Если расширение не поддерживается, возвращаем минимальную инфу
        if not file_type:
            return {"path": str(file_path), "content": "", "status": "unsupported"}

        try:
            parser = self._get_parser(file_type)
            if parser:
                logger.info(f"Парсинг: {file_path.name}")
                # Вызываем parse, который уже возвращает заполненный словарь
                return parser.parse(file_path)
                
        except Exception as e:
            logger.error(f"Ошибка в {file_path.name}: {e}")
            return {
                "path": str(file_path), 
                "content": f"Error: {e}", 
                "status": "error"
            }


    def scan_directory(self, root_path: str):
        """Рекурсивный обход и парсинг"""
        root = Path(root_path)
        if not root.exists():
            logger.error(f"Directory {root_path} does not exist")
            return []

        # Собираем все файлы, которые мы умеем обрабатывать
        files_to_process = [
            f for f in root.rglob('*') 
            if f.is_file() and f.suffix.lower() in self.extension_map
        ]
        
        logger.info(f"Found {len(files_to_process)} supported files.")
        
        # Для хакатона: если данных много (3ГБ), лучше использовать 
        # обычный цикл или ThreadPool для I/O задач. 
        # OCR задачи лучше пускать в ProcessPool.
        final_results = []
        for file in files_to_process:
            final_results.append(self.process_file(file))
            
        return final_results
