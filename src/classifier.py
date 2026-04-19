class Classifier:
    def classify(self, cats: dict[str, int]) -> str:
        if not cats:
            return "NO_PDN"

        total = sum(cats.values())
        if total <= 0:
            return "NO_PDN"

        if cats.get("special", 0) > 0 or cats.get("biometric", 0) > 0:
            return "УЗ-1"

        if cats.get("card", 0) > 0 or cats.get("bank_account", 0) > 0 or total > 50:
            return "УЗ-2"

        if any(cats.get(key, 0) > 0 for key in ("passport", "snils", "inn", "driver_license")):
            return "УЗ-3"

        return "УЗ-4"