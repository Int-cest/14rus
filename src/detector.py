import re
from collections import defaultdict
from validators import luhn_check, validate_snils


class Detector:
    def __init__(self):
        # --- BASIC PATTERNS ---
        self.patterns = {
            # контакты
            "email": re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b"),
            "phone": re.compile(r"\+?\d[\d\-\(\) ]{8,}\d"),

            # ФИО (простое приближение)
            "fio": re.compile(r"\b[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+\b"),

            # дата рождения
            "birth_date": re.compile(r"\b\d{2}[./-]\d{2}[./-]\d{2,4}\b"),

            # гос id
            "snils": re.compile(r"\b\d{3}-\d{3}-\d{3} \d{2}\b"),
            "inn": re.compile(r"\b(\d{10}|\d{12})\b"),
            "passport": re.compile(r"\b\d{4} \d{6}\b"),
            "driver_license": re.compile(r"\b\d{2} \d{2} \d{6}\b"),

            # платежи
            "card": re.compile(r"\b\d{13,19}\b"),
            "bik": re.compile(r"\b\d{9}\b"),
            "bank_account": re.compile(r"\b\d{20}\b"),
            "cvv": re.compile(r"(cvv|cvc)[\s:]*\d{3}", re.IGNORECASE),

            # MRZ
            "mrz": re.compile(r"[A-Z0-9<]{30,}")
        }

        self.address_keywords = ["г.", "ул.", "д.", "кв.", "обл."]

        self.biometric_keywords = [
            "отпечаток пальца",
            "радужная оболочка",
            "голосовой образец",
            "биометрия"
        ]

        self.special_keywords = [
            "диагноз", "болезнь", "инвалидность",
            "религия", "вероисповедание",
            "политические взгляды",
            "национальность", "этнический"
        ]

    def detect(self, text: str):
        if not text:
            return {}

        results = defaultdict(list)
        text_lower = text.lower()

        # --- REGEX DETECTION ---
        for key, pattern in self.patterns.items():
            matches = pattern.findall(text)

            # фильтры
            if key == "card":
                matches = [m for m in matches if luhn_check(m)]

            if key == "snils":
                matches = [m for m in matches if validate_snils(m)]

            # фильтр БИК (по контексту)
            if key == "bik":
                matches = [
                    m for m in matches
                    if "бик" in text_lower
                ]

            # фильтр банковского счета
            if key == "bank_account":
                matches = [
                    m for m in matches
                    if "счет" in text_lower or "р/с" in text_lower
                ]

            if matches:
                results[key].extend(matches)

        # --- ADDRESS ---
        for word in self.address_keywords:
            if word in text_lower:
                results["address"].append(word)
                break

        # --- BIOMETRIC ---
        for word in self.biometric_keywords:
            if word in text_lower:
                results["biometric"].append(word)

        # --- SPECIAL ---
        for word in self.special_keywords:
            if word in text_lower:
                results["special"].append(word)

        return dict(results)