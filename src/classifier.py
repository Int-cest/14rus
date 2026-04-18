class Classifier:
    def classify(self, detected):
        if not detected:
            return "NO_PDN"

        counts = {k: len(v) for k, v in detected.items()}
        total = sum(counts.values())

        # УЗ-1
        if "special" in detected or "biometric" in detected:
            return "УЗ-1"

        # УЗ-2
        if (
            counts.get("card", 0) > 0 or
            counts.get("bank_account", 0) > 0 or
            total > 50
        ):
            return "УЗ-2"

        # УЗ-3
        if any(k in detected for k in ["passport", "snils", "inn", "driver_license"]):
            return "УЗ-3"

        # УЗ-4
        if total > 0:
            return "УЗ-4"

        return "NO_PDN"