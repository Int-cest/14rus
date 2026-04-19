import re
from typing import Dict, List, Any


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

        self.CARD_RE = re.compile(r"(?:(?:\d[ -]*?){13,19})")

        self.BIO_KEYWORDS = [
            "биометр", "face", "iris", "finger", "voice", "селфи"
        ]

        self.SPECIAL_KEYWORDS = [
            "диагноз", "болезнь", "инвалид", "медицин", "вич", "полит"
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