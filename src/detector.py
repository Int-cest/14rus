import re
from typing import Dict, List, Tuple


# ---------------- VALIDATORS ----------------

def luhn_check(number: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", number)]
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


def inn_valid(inn: str) -> bool:
    nums = re.sub(r"\D", "", inn)

    if len(nums) == 10:
        w = [2,4,10,3,5,9,4,6,8]
        c = sum(int(nums[i]) * w[i] for i in range(9)) % 11 % 10
        return c == int(nums[9])

    if len(nums) == 12:
        w1 = [7,2,4,10,3,5,9,4,6,8]
        w2 = [3,7,2,4,10,3,5,9,4,6,8]
        c1 = sum(int(nums[i]) * w1[i] for i in range(11)) % 11 % 10
        c2 = sum(int(nums[i]) * w2[i] for i in range(11)) % 11 % 10
        return c1 == int(nums[10]) and c2 == int(nums[11])

    return False


def snils_valid(snils: str) -> bool:
    nums = re.sub(r"\D", "", snils)
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


# ---------------- DETECTOR ----------------

class Detector:

    def __init__(self, debug: bool = True):
        self.debug = debug

        # regex
        self.EMAIL_RE = re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
        self.PHONE_RE = re.compile(r"(?:(?:\+7|8)\s*\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2})")
        self.FIO_RE = re.compile(r"\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?\b")

        self.INN_RE = re.compile(r"\b\d{10,12}\b")
        self.SNILS_RE = re.compile(r"\b\d{3}-\d{3}-\d{3}\s?\d{2}\b")

        self.CARD_RE = re.compile(r"(?:\d[ -]*?){13,19}")

        self.PASSPORT_RE = re.compile(r"\b\d{2}\s?\d{2}\s?\d{6}\b")

        self.BIO_KEYWORDS = [
            "биометр", "отпечат", "радуж", "ирис", "лицев", "селфи",
                "face", "finger", "iris", "voiceprint", "геометрия"
        ]
        self.SPECIAL_KEYWORDS = ['диагноз', 'религ', 'инвалид', 'вероиспевед']


    # ---------- HELPERS ----------

    def _context(self, text: str, start: int, end: int = None, size: int = 40):
        if end is None:
            end = start
        left = max(0, start - size)
        right = min(len(text), end + size)
        return text[left:right]

    def _log(self, trace, category, value, decision, reason, context):
        if self.debug:
            trace.append({
                "category": category,
                "value": value,
                "decision": decision,   # accepted / rejected
                "reason": reason,
                "context": context
            })

    def _empty(self):
        return {
            "обычные": 0,
            "государственные": 0,
            "платёжные": 0,
            "биометрические": 0,
            "специальные": 0
        }

    # ---------- MAIN ----------

    def detect(self, text: str) -> Tuple[Dict, List]:
        if not text:
            return self._empty(), []

        low = text.lower()
        cats = self._empty()
        trace = []

        # -------- EMAIL --------
        for m in self.EMAIL_RE.finditer(text):
            cats["обычные"] += 1
            self._log(trace, "обычные", m.group(), "accepted", "email", self._context(text, m.start()))

        # -------- PHONE --------
        for m in self.PHONE_RE.finditer(text):
            cats["обычные"] += 1
            self._log(trace, "обычные", m.group(), "accepted", "phone", self._context(text, m.start()))

        # -------- FIO --------
        for m in self.FIO_RE.finditer(text):
            val = m.group()
            if len(val.split()) >= 2:
                cats["обычные"] += 1
                self._log(trace, "обычные", val, "accepted", "fio", self._context(text, m.start()))
            else:
                self._log(trace, "обычные", val, "rejected", "too short", self._context(text, m.start()))

        # -------- INN --------
        for m in self.INN_RE.finditer(text):
            val = m.group()
            if inn_valid(val):
                cats["государственные"] += 1
                self._log(trace, "государственные", val, "accepted", "valid INN", self._context(text, m.start()))
            else:
                self._log(trace, "государственные", val, "rejected", "invalid INN", self._context(text, m.start()))

        # -------- SNILS --------
        for m in self.SNILS_RE.finditer(text):
            val = m.group()
            if snils_valid(val):
                cats["государственные"] += 1
                self._log(trace, "государственные", val, "accepted", "valid SNILS", self._context(text, m.start()))
            else:
                self._log(trace, "государственные", val, "rejected", "invalid SNILS", self._context(text, m.start()))

        # -------- PASSPORT --------
        for m in self.PASSPORT_RE.finditer(text):
            val = m.group()
            ctx = self._context(text, m.start(), m.end(), 60)

            if self.PASSPORT_CONTEXT_RE.search(ctx):
                cats["государственные"] += 1
                self._log(trace, "государственные", val, "accepted", "passport with local context", ctx)
            else:
                self._log(trace, "государственные", val, "rejected", "no local passport context", ctx)

        # -------- CARD --------
        for m in self.CARD_RE.finditer(text):
            raw = m.group()
            digits = re.sub(r"\D", "", raw)
            ctx = self._context(text, m.start(), m.end(), 60)

            if not (13 <= len(digits) <= 19):
                continue

            if not luhn_check(digits):
                self._log(trace, "платёжные", digits, "rejected", "failed luhn", ctx)
                continue

            if not self.CARD_CONTEXT_RE.search(ctx):
                self._log(trace, "платёжные", digits, "rejected", "no card context", ctx)
                continue

            cats["платёжные"] += 1
            self._log(trace, "платёжные", digits, "accepted", "valid card + context", ctx)

        # -------- BIO --------
        for p in self.BIO_PATTERNS:
            m = p.search(low)
            if m:
                cats["биометрические"] += 1
                self._log(trace, "биометрические", m.group(), "accepted", "keyword-pattern", self._context(low, m.start(), m.end()))

        # -------- SPECIAL --------
        for p in self.SPECIAL_PATTERNS:
            m = p.search(low)
            if m:
                cats["специальные"] += 1
                self._log(trace, "специальные", m.group(), "accepted", "keyword-pattern", self._context(low, m.start(), m.end()))

        return cats, trace