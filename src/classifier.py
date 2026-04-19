class Classifier:
    def classify(self, cats: Dict[str, int]) -> str:
        total = sum(cats.values())
        distinct = sum(1 for v in cats.values() if v > 0)
        has_special = cats["специальные"] > 0
        has_bio = cats["биометрические"] > 0
        has_pay = cats["платёжные"] > 0
        has_gov = cats["государственные"] > 0
        has_common = cats["обычные"] > 0

        # --- ЭТАЛОННАЯ ЛОГИКА УЗ ---
        if has_special or has_bio:
            return "УЗ-1" if (total >= 5 or distinct >= 2) else "УЗ-2"
        if has_pay or has_gov:
            return "УЗ-2" if (total >= 5 or distinct >= 2) else "УЗ-3"
        if has_common:
            return "УЗ-3" if (total >= 5 or distinct >= 2) else "УЗ-4"
        return "NO_PDN"