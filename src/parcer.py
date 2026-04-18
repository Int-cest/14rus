from abc import ABC, abstractmethod
from pathlib import Path
import logging
import easyocr
import whisper
import cv2

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
        self._get_ocr_reader()

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

class Videos(Parser):
    def __init__(
        self,
        use_ocr: bool = True,
        lang: str = "rus+eng",
        frame_interval: int = 30,
        max_frames: int = 200
    ):
        self.use_ocr = use_ocr
        self.lang = lang
        self.frame_interval = frame_interval
        self.max_frames = max_frames
    
    def parse(self, data_path: Path) -> str:
        if not self.use_ocr:
            return ""

        texts = []

        try:
            cap = cv2.VideoCapture(str(data_path))

            if not cap.isOpened():
                logger.info(f"[Videos Parser] Cannot open {data_path}")
                return ""

            frame_count = 0
            processed_frames = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # берём не каждый кадр
                if frame_count % self.frame_interval == 0:
                    try:
                        text = pytesseract.image_to_string(frame, lang=self.lang)
                        text = text.strip()

                        if len(text) > 5:
                            texts.append(text)

                        processed_frames += 1

                        if processed_frames >= self.max_frames:
                            break

                    except Exception as e:
                        logger.debug(f"OCR error on frame: {e}")

                frame_count += 1

            cap.release()

            # объединяем текст
            return "\n".join(texts)

        except Exception as e:
            logger.info(f"[Videos Parser] Error processing {data_path}: {e}")
            return ""