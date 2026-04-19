from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PATH_DATA = PROJECT_ROOT / "datasets" / "test"

LOG_DIR = PROJECT_ROOT / "logs"
LOG_INFO_FILE = LOG_DIR / "parser_info.log"
LOG_ERROR_FILE = LOG_DIR / "parser_error.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

OCR_LANGUAGES = ("ru", "en")
OCR_GPU = True
OCR_BATCH_SIZE = 8
OCR_WORKERS = 0
OCR_VIDEO_MAX_SIDE = 1280

VIDEO_FRAME_INTERVAL = 30
VIDEO_MAX_FRAMES = 200

EXTENSION_MAP = {
    ".csv": "structured",
    ".json": "structured",
    ".parquet": "structured",
    ".pdf": "document",
    ".docx": "document",
    ".doc": "document",
    ".rtf": "document",
    ".txt": "document",
    ".md": "document",
    ".ipynb": "document",
    ".xls": "document",
    ".jpg": "image",
    ".png": "image",
    ".tif": "image",
    ".tiff": "image",
    ".gif": "image",
    ".mp4": "video",
    ".html": "web",
}
