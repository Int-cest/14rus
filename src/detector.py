import re
from typing import Dict, List, Any

# --- Вспомогательные валидаторы и функции ---
def luhn_check(number: str) -> bool:
    digits = [int(d) for d in re.sub(r'\D', '', number)]
    if not (13 <= len(digits) <= 19):
        return False
    s = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return s % 10 == 0

def snils_valid(snils: str) -> bool:
    nums = re.sub(r'\D', '', snils)
    if len(nums) != 11:
        return False
    base = [int(x) for x in nums[:9]]
    check = int(nums[9:])
    s = sum((9 - i) * d for i, d in enumerate(base))
    if s < 100:
        c = s
    elif s in (100, 101):
        c = 0
    else:
        c = s % 101
        if c == 100:
            c = 0
    return c == check

def inn_valid(inn: str) -> bool:
    nums = re.sub(r'\D', '', inn)
    if len(nums) == 10:
        w = [2,4,10,3,5,9,4,6,8]
        c = sum(int(nums[i]) * w[i] for i in range(9)) % 11 % 10
        return c == int(nums[9])
    elif len(nums) == 12:
        w1 = [7,2,4,10,3,5,9,4,6,8,0]
        w2 = [3,7,2,4,10,3,5,9,4,6,8,0]
        c1 = sum(int(nums[i]) * w1[i] for i in range(11)) % 11 % 10
        c2 = sum(int(nums[i]) * w2[i] for i in range(11)) % 11 % 10
        return c1 == int(nums[10]) and c2 == int(nums[11])
    return False

def has_context(text: str, idx: int, window: int, *keywords: str) -> bool:
    start = max(0, idx - window)
    end = min(len(text), idx + window)
    chunk = text[start:end]
    return any(k in chunk for k in keywords)

class Detector:
    def __init__(self, debug: bool = False):
        self.debug = debug

        # --- regex ---
        self.EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b")
        self.PHONE_RE = re.compile(r"(?:(?:\+7|8)\s*\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2})")
        self.FIO_RE = re.compile(r"\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?\b")
        self.DOB_RE = re.compile(r"\b(\d{2}[./]\d{2}[./]\d{4})\b")
        self.INDEX_RE = re.compile(r"\b\d{6}\b")

        self.SNILS_RE = re.compile(r"\b\d{3}-\d{3}-\d{3}\s?\d{2}\b")
        self.INN10_RE = re.compile(r"(?<!\d)\d{10}(?!\d)")
        self.INN12_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")
        self.PASSPORT_RE = re.compile(r"(?:(?<!\d)\d{2}\s?\d{2}\s?\d{6}(?!\d))")

        self.MRZ_RE = re.compile(r"[P|V|C]<[A-Z<]{2}")
        self.DL_RE = re.compile(r"(?<!\d)\d{10,12}(?!\d)")  

        self.CARD_RE = re.compile(r"(?:(?:\d[ -]*?){13,19})")
        self.CVV_RE = re.compile(r"\b(CVV|CVC|CVV2)\b", re.IGNORECASE)
        self.RS_RE = re.compile(r"(?i)(?:р/с|расч[её]тн(?:ый)?\s+сч[её]т)[^\d]*(\d{20})")
        self.BIK_RE = re.compile(r"(?i)бик[^\d]*(\d{9})")

        self.BIO_KEYWORDS = [
            'биометр', 'отпечат', 'радуж', 'ирис', 'лицев', 'селфи', 'faceid', 'fingerprint', 'iris', 'voiceprint', 'голосов', 'геометрия лица'
        ]

        self.SPECIAL_KEYWORDS = [
            'диагноз', 'анамнез', 'инвалид', 'здоровь', 'медицин', 'психиатр', 'вич', 'религ', 'вероисповед', 'политическ', 'партия', 'интим', 'сексуаль'
        ]

    # ---------------- DEBUG HELPERS ----------------

    def _log(self, store: List, category: str, value: str, reason: str, context: str):
        if self.debug:
            store.append({
                "category": category,
                "value": value,
                "reason": reason,
                "context": context
            })

    def _has_context(self, low_text: str, start: int, window: int, *keywords) -> bool:
        ctx = low_text[max(0, start-window): start+window]
        return any(k in ctx for k in keywords)

    def _empty(self):
        return {
            "обычные": 0,
            "государственные": 0,
            "платёжные": 0,
            "биометрические": 0,
            "специальные": 0
        }

    # ---------------- MAIN ----------------

    def detect(self, text: str):
        if not text:
            return self._empty(), []

        low = text.lower()
        cats = self._empty()
        trace = []

        # -------- EMAIL --------
        for m in self.EMAIL_RE.finditer(text):
            cats["обычные"] += 1
            self._log(trace, "обычные", m.group(), "email detected", text[m.start()-20:m.end()+20])

        # -------- PHONE --------
        for m in self.PHONE_RE.finditer(text):
            cats["обычные"] += 1
            self._log(trace, "обычные", m.group(), "phone detected", text[m.start()-20:m.end()+20])

        # -------- FIO --------
        for m in self.FIO_RE.finditer(text):
            if len(m.group()) < 40:
                cats["обычные"] += 1
                self._log(trace, "обычные", m.group(), "fio pattern", text[m.start()-20:m.end()+20])

        # -------- DOB --------
        for m in self.DOB_RE.finditer(text):
            if self._has_context(low, m.start(), 40, "дата рождения", "родил"):
                cats["обычные"] += 1
                self._log(trace, "обычные", m.group(), "dob with context", text[m.start()-20:m.end()+20])
            else:
                self._log(trace, "обычные", m.group(), "dob without context (ignored risk)", text[m.start()-20:m.end()+20])

        # -------- INDEX --------
        for m in self.INDEX_RE.finditer(text):
            if self._has_context(low, m.start(), 40, "улица", "дом", "город"):
                cats["обычные"] += 1
                self._log(trace, "обычные", m.group(), "index with address context", text[m.start()-20:m.end()+20])

        # -------- INN / SNILS --------
        for m in self.INN10_RE.finditer(text):
            cats["государственные"] += 1
            self._log(trace, "государственные", m.group(), "INN10 raw match", text[m.start()-20:m.end()+20])

        for m in self.INN12_RE.finditer(text):
            cats["государственные"] += 1
            self._log(trace, "государственные", m.group(), "INN12 raw match", text[m.start()-20:m.end()+20])

        for m in self.SNILS_RE.finditer(text):
            cats["государственные"] += 1
            self._log(trace, "государственные", m.group(), "SNILS detected", text[m.start()-20:m.end()+20])

        # -------- PASSPORT --------
        for m in self.PASSPORT_RE.finditer(text):
            if self._has_context(low, m.start(), 50, "паспорт", "серия"):
                cats["государственные"] += 1
                self._log(trace, "государственные", m.group(), "passport with context", text[m.start()-20:m.end()+20])
            else:
                self._log(trace, "государственные", m.group(), "passport without context (risky)", text[m.start()-20:m.end()+20])

        # -------- CARD --------
        for m in self.CARD_RE.finditer(text):
            digits = re.sub(r"\D", "", m.group())

            if 13 <= len(digits) <= 19:
                cats["платёжные"] += 1
                self._log(trace, "платёжные", digits, "possible card (no luhn here debug mode)", text[m.start()-20:m.end()+20])

        # -------- BIO --------
        if any(k in low for k in self.BIO_KEYWORDS):
            cats["биометрические"] += 1
            self._log(trace, "биометрические", "keyword", "bio keyword hit", low[:120])

        # -------- SPECIAL --------
        if any(k in low for k in self.SPECIAL_KEYWORDS):
            cats["специальные"] += 1
            self._log(trace, "специальные", "keyword", "special keyword hit", low[:120])

        return cats, trace