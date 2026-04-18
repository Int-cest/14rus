from pathlib import Path
from collections import Counter

from config import PATH_DATA

def get_extensions_dict_fast(root_path):
    """Быстрый словарь расширений с подсчётом"""
    extensions = Counter()
    
    for file_path in Path(root_path).rglob('*'):
        if file_path.is_file() and file_path.suffix:
            extensions[file_path.suffix.lower()] += 1
    
    return dict(extensions)

# Использование
ext_dict = get_extensions_dict_fast(PATH_DATA)
print("Все расширения в датасете:")
for ext, count in sorted(ext_dict.items(), key=lambda x: x[1], reverse=True):
    print(f"  {ext}: {count} файлов")