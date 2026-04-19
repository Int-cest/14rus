import re
from typing import Dict, List

class Detector:
    def __init__(self):
        # --- regex ---
        self.EMAIL_RE = re.compile(r"\b[a-zA-Z0-9.\_%+-\]+@[a-zA-Z0-9.-\]+\.[A-Za-z]{2,}\b")
        self.PHONE_RE = re.compile(r"(?:(?:\+7|8)\s*\(\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2})")
        self.FIO_RE = re.compile(r"\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?\b")
        self.DOB_RE = re.compile(r"\b(\d{2}[./]\d{2}[./]\d{4})\b") # Обновлен
        self.INDEX_RE = re.compile(r"\b\d{6}\b")

        self.SNILS_RE = re.compile(r"\b\d{3}-\d{3}-\d{3}\s?\d{2}\b")
        self.INN10_RE = re.compile(r"(?<!\d)\d{10}(?!\d)")
        self.INN12_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")
        self.PASSPORT_RE = re.compile(r"(?:(?<!\d)\d{2}\s?\d{2}\s?\d{6}(?!\d))")
        self.MRZ_RE = re.compile(r"[P|V|C]<[A-Z<]{2}") # Обновлен
        self.DL_RE = re.compile(r"(?<!\d)\d{10,12}(?!\d)") # Добавлен

        self.CARD_RE = re.compile(r"(?:(?:\d[ -]*?){13,19})")
        self.CVV_RE = re.compile(r"\b(CVV|CVC|CVV2)\b", re.IGNORECASE) # Добавлен
        self.RS_RE = re.compile(r"(?i)(?:р/с|расч[её]тн(?:ый)?\s+сч[её]т)[^\d]*(\d{20})") # Обновлен
        self.BIK_RE = re.compile(r"(?i)бик[^\d]*(\d{9})") # Обновлен

        # --- keywords ---
        # Объединены и расширены ключевые слова для биометрических данных
        self.BIO_KEYWORDS: List[str] = list(set([
            "биометр", "face", "iris", "finger", "voice", "селфи",
            'отпечат', 'радуж', 'ирис', 'лицев', 'faceid', 'fingerprint', 'iris', 'voiceprint', 'голосов', 'геометрия лица'
        ]))
        # Объединены и расширены ключевые слова для специальных данных
        self.SPECIAL_KEYWORDS: List[str] = list(set([
            "диагноз", "болезнь", "инвалид", "религ", "полит",
            'анамнез', 'здоровь', 'медицин', 'психиатр', 'вич', 'вероисповед', 'политическ', 'партия', 'интим', 'сексуаль'
        ]))

    # --- Приватные вспомогательные методы (аналоги функций организаторов) ---

    def _count_occurrences(self, pattern: re.Pattern, text: str) -> int:
        """Подсчитывает количество вхождений паттерна в тексте."""
        return len(list(pattern.finditer(text)))

    def _has_context(self, low_text: str, match_start: int, window_size: int, *keywords: str) -> bool:
        """
        Проверяет наличие ключевых слов в окне вокруг найденного совпадения.
        low_text: текст в нижнем регистре.
        match_start: начальная позиция совпадения.
        window_size: размер окна для поиска контекста.
        keywords: ключевые слова для поиска.
        """
        start = max(0, match_start - window_size)
        end = min(len(low_text), match_start + window_size)
        context = low_text[start:end]
        return any(k in context for k in keywords)

    def _luhn_check(self, card_number: str) -> bool:
        """
        Проверяет номер карты с помощью алгоритма Луна.
        """
        digits = [int(d) for d in card_number if d.isdigit()]
        if not digits:
            return False
        
        s = 0
        is_second = False
        for digit in digits[::-1]:
            if is_second:
                digit *= 2
            s += digit if digit < 10 else digit - 9
            is_second = not is_second
        return s % 10 == 0

    def _snils_valid(self, snils_str: str) -> bool:
        """
        ЗАГЛУШКА: Здесь должна быть реальная логика валидации СНИЛС
        по контрольной сумме.
        """
        # Удаляем все нецифровые символы
        digits = ''.join(filter(str.isdigit, snils_str))
        if len(digits) != 11:
            return False
        # Примерная логика: пока просто проверяем длину
        return True 

    def _inn_valid(self, inn_str: str) -> bool:
        """
        ЗАГЛУШКА: Здесь должна быть реальная логика валидации ИНН
        по контрольной сумме.
        """
        digits = ''.join(filter(str.isdigit, inn_str))
        if len(digits) not in [10, 12]:
            return False
        # Примерная логика: пока просто проверяем длину
        return True

    # --- Основной метод обнаружения ---

    def detect(self, text: str) -> Dict[str, int]:
        if not text:
            return self._empty()

        low = text.lower()
        cats = self._empty()

        # --- обычные ---
        cats["обычные"] += self._count_occurrences(self.EMAIL_RE, text)
        cats["обычные"] += self._count_occurrences(self.PHONE_RE, text)
        cats["обычные"] += min(5, self._count_occurrences(self.FIO_RE, text))

        for m in self.DOB_RE.finditer(text):
            if self._has_context(low, m.start(), 40, 'дата рождения', 'родил'):
                cats["обычные"] += 1
        
        for m in self.INDEX_RE.finditer(text):
            if self._has_context(low, m.start(), 40, 'ул', 'улица', 'просп', 'пер', 'дом', 'квартира', 'город', 'г.'):
                cats["обычные"] += 1

        # --- гос ---
        for m in self.SNILS_RE.finditer(text):
            if self._snils_valid(m.group(0)):
                cats["государственные"] += 1

        for m in self.INN10_RE.finditer(text):
            s = m.group(0)
            if self._inn_valid(s):
                cats["государственные"] += 1

        for m in self.INN12_RE.finditer(text):
            s = m.group(0)
            if self._inn_valid(s):
                cats["государственные"] += 1
        
        for m in self.PASSPORT_RE.finditer(text):
            if self._has_context(low, m.start(), 50, 'паспорт', 'серия', 'номер', 'код подразделения'):
                cats["государственные"] += 1
        
        for m in self.DL_RE.finditer(text):
            if self._has_context(low, m.start(), 30, 'водител', 'удостовер'):
                cats["государственные"] += 1

        if self.MRZ_RE.search(text):
            cats["государственные"] += 1

        # --- платежные ---
        for m in self.CARD_RE.finditer(text):
            raw = m.group(0)
            digits = re.sub(r'\D', '', raw)
            if 13 <= len(digits) <= 19 and self._luhn_check(raw):
                if self._has_context(low, m.start(), 40, 'visa', 'mastercard', 'карта', 'cvv', 'cvc', 'номер карты'):
                    cats["платёжные"] += 1
        
        cats["платёжные"] += self._count_occurrences(self.RS_RE, text)
        cats["платёжные"] += self._count_occurrences(self.BIK_RE, text)

        if self.CVV_RE.search(text):
            cats["платёжные"] += 1

        # --- био / спец ---
        if any(k in low for k in self.BIO_KEYWORDS):
            cats["биометрические"] += 1

        if any(k in low for k in self.SPECIAL_KEYWORDS):
            cats["специальные"] += 1

        return cats

    def _empty(self):
        return {
            "обычные": 0,
            "государственные": 0,
            "платёжные": 0,
            "биометрические": 0,
            "специальные": 0
        }