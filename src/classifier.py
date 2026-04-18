import re
from collections import defaultdict
from validators import luhn_check, validate_snils


class Detector:
    def __init__(self):
        self.patterns = {
            "email": re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b"),
            "phone": re.compile(r"\+?\d[\d\-\(\) ]{8,}\d"),
            "snils": re.compile(r"\b\d{3}-\d{3}-\d{3} \d{2}\b"),
            "inn": re.compile(r"\b(\d{10}|\d{12})\b"),
            "passport": re.compile(r"\b\d{4} \d{6}\b"),
            "card": re.compile(r"\b\d{13,19}\b"),
        }

        self.biometric = [
            "отпечаток пальца",
            "радужная оболочка",
            "голосовой образец",
            "биометрия"
        ]

        self.special = [
            "диагноз",
            "болезнь",
            "религия",
            "политические взгляды",
            "национальность"
        ]

    def detect(self, text: str):
        results = defaultdict(list)

        text_lower = text.lower()

        # regex
        for key, pattern in self.patterns.items():
            matches = pattern.findall(text)

            if key == "card":
                matches = [m for m in matches if luhn_check(m)]

            if key == "snils":
                matches = [m for m in matches if validate_snils(m)]

            if matches:
                results[key].extend(matches)

        # keywords
        for word in self.biometric:
            if word in text_lower:
                results["biometric"].append(word)

        for word in self.special:
            if word in text_lower:
                results["special"].append(word)

        return results