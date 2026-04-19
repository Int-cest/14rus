import re
from typing import Dict


class Detector:
    def __init__(self):
        # Категории и ключи выровнены под чекпоинт datasets/data/test.csv.
        self.patterns: dict[str, re.Pattern] = {
            "email": re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b"),
            "phone": re.compile(r"\+?\d[\d\-\(\) ]{8,}\d"),
            "fio": re.compile(r"\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b"),
            "birth_date": re.compile(r"\b\d{2}[./-]\d{2}[./-]\d{2,4}\b"),
            "snils": re.compile(r"\b\d{3}-\d{3}-\d{3}\s\d{2}\b"),
            "inn": re.compile(r"\b(?:\d{10}|\d{12})\b"),
            "passport": re.compile(r"\b\d{4}\s\d{6}\b"),
            "driver_license": re.compile(r"\b\d{2}\s\d{2}\s\d{6}\b"),
            "card": re.compile(r"\b\d{13,19}\b"),
            "bik": re.compile(r"(?i)(?:бик)[^\d]*(\d{9})"),
            "bank_account": re.compile(r"(?i)(?:р/с|расч[её]тн(?:ый)?\s+сч[её]т|корр?\.?\s*сч[её]т)[^\d]*(\d{20})"),
            "cvv": re.compile(r"(?i)\b(?:cvv|cvc)[\s:]*\d{3}\b"),
            "mrz": re.compile(r"[A-Z0-9<]{30,}"),
        }

        self.address_keywords = ["адрес", "улица", "ул.", "просп", "дом", "кв.", "г."]
        self.card_keywords = ["карта", "card", "visa", "mastercard", "cvv", "cvc"]
        self.biometric_keywords = ["отпечат", "радуж", "голос", "биометр"]
        self.special_keywords = [
            "диагноз",
            "болезн",
            "инвалид",
            "религ",
            "вероисповед",
            "политическ",
            "националь",
            "этническ",
        ]

    def _luhn_check(self, value: str) -> bool:
        digits = [int(ch) for ch in re.sub(r"\D", "", value)]
        if len(digits) < 13:
            return False

        checksum = 0
        is_second = False
        for digit in reversed(digits):
            if is_second:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
            is_second = not is_second
        return checksum % 10 == 0

    def _validate_snils(self, value: str) -> bool:
        digits = re.sub(r"\D", "", value)
        if len(digits) != 11:
            return False

        base = digits[:9]
        control = int(digits[9:])
        checksum = sum(int(base[i]) * (9 - i) for i in range(9))

        if checksum < 100:
            expected = checksum
        elif checksum in (100, 101):
            expected = 0
        else:
            expected = checksum % 101
            if expected == 100:
                expected = 0

        return control == expected

    def detect(self, text: str) -> Dict[str, int]:
        if not text:
            return {}

        found: Dict[str, int] = {}
        low = text.lower()

        for key, pattern in self.patterns.items():
            matches = [m.group(0) for m in pattern.finditer(text)]

            if key == "card":
                if not any(word in low for word in self.card_keywords):
                    matches = []
                matches = [m for m in matches if self._luhn_check(m)]
            elif key == "snils":
                matches = [m for m in matches if self._validate_snils(m)]

            if matches:
                found[key] = len(matches)

        if any(word in low for word in self.address_keywords):
            found["address"] = 1

        if any(word in low for word in self.biometric_keywords):
            found["biometric"] = 1

        if any(word in low for word in self.special_keywords):
            found["special"] = 1

        return found