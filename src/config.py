from pathlib import Path


# Data path used by notebook/pipeline.
PATH_DATA = r"..\datasets\test"


# Project paths for logs and service files.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_INFO_FILE = LOG_DIR / "parser_info.log"
LOG_ERROR_FILE = LOG_DIR / "parser_error.log"


# Logging setup.
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_COLORS = {
	"DEBUG": "\033[37m",    # white
	"INFO": "\033[34m",     # blue
	"WARNING": "\033[33m",  # yellow
	"ERROR": "\033[31m",    # red
	"CRITICAL": "\033[35m", # magenta
}
LOG_COLOR_RESET = "\033[0m"


# OCR and text parsing.
OCR_LANGUAGES = ("ru", "en")
OCR_GPU = False
TEXT_ENCODINGS = ("utf-8", "utf-8-sig", "cp1251", "latin-1")


# Video OCR sampling.
VIDEO_FRAME_INTERVAL = 30
VIDEO_MAX_FRAMES = 200


# File routing by extension.
EXTENSION_MAP = {
	# Structured data
	".csv": "structured",
	".json": "structured",
	".parquet": "structured",

	# Documents
	".pdf": "document",
	".docx": "document",
	".doc": "document",
	".rtf": "document",
	".txt": "document",
	".md": "document",
	".xls": "document",
	".xlsx": "document",

	# Images
	".jpg": "image",
	".jpeg": "image",
	".png": "image",
	".tif": "image",
	".tiff": "image",
	".gif": "image",

	# Video
	".mp4": "video",

	# Web
	".html": "web",
}