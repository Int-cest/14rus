from pathlib import Path

def scan_files(root_path: str):
    """Рекурсивно обходит папку и возвращает пути ко всем файлам."""
    root = Path(root_path)
    # rglob('*') находит всё рекурсивно
    for file_path in root.rglob('*'):
        if file_path.is_file():
            # Сразу проверяем размер, чтобы не пытаться открыть 10-гигабайтный файл
            if file_path.stat().st_size < 100 * 1024 * 1024: # Лимит 100 МБ
                yield file_path
            else:
                print(f"Пропущен огромный файл: {file_path}")

import pandas as pd
import pytesseract
from PIL import Image

from striprtf.striprtf import rtf_to_text

# Инициализируем тяжелые модели ОДИН РАЗ (глобально), чтобы не грузить их на каждый файл


def extract_text_from_file(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    
    # 1. Офисные документы
    if ext == '.pdf':
        import fitz
        doc = fitz.open(file_path)
        text = " ".join([page.get_text() for page in doc])
        return text
    elif ext == '.docx':
        from docx import Document
        doc = Document(file_path)
        return " ".join([p.text for p in doc.paragraphs])
    elif ext in ['.xls', '.xlsx']:
        # Читаем Excel как строки, чтобы не потерять номера телефонов/ИНН (Excel не любит длинные числа)
        df = pd.read_excel(file_path, dtype=str, keep_default_na=False)
        return df.to_string(na_rep='') # Конвертируем таблицу в текст
        
    # 2. Структурированные данные
    elif ext == '.csv':
        df = pd.read_csv(file_path, dtype=str)
        return df.to_string()
    elif ext == '.parquet':
        df = pd.read_parquet(file_path)  # или rugo, если pandas тормозит
        return df.to_string()
        
    # 3. Веб и разметка
    elif ext == '.html':
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(file_path.read_text(encoding='utf-8', errors='ignore'), 'html.parser')
        return soup.get_text()
    elif ext == '.rtf':
        raw = file_path.read_text(encoding='utf-8', errors='ignore')
        return rtf_to_text(raw)
        
    # 4. Изображения (OCR)
    elif ext in ['.jpg', '.jpeg', '.png', '.tif']:
        # Вариант 1: EasyOCR (лучше для русских документов) [citation:3]
        result = ocr_reader.readtext(str(file_path), detail=0, paragraph=True)
        return " ".join(result)
        # Вариант 2: Tesseract (бесплатно, но ставится отдельно)
        # img = Image.open(file_path)
        # return pytesseract.image_to_string(img, lang='rus')
        
    # 5. Видео (транскрипция)
    elif ext == '.mp4':
        # Whisper принимает аудио, поэтому конвертировать видео на лету сложно.
        # Упрощенно: вытаскиваем аудиодорожку через ffmpeg в буфер
        import subprocess, tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            # Извлекаем аудио в WAV
            subprocess.run(['ffmpeg', '-i', str(file_path), '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', tmp.name], check=True, capture_output=True)
            result = whisper_model.transcribe(tmp.name, language='ru')
            os.unlink(tmp.name)
            return result["text"]
            
    # 6. Текстовые файлы (plain text, json и пр.)
    else:
        try:
            return file_path.read_text(encoding='utf-8', errors='ignore')
        except:
            return ""