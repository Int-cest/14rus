import pandas as pd
import json


def _nonzero_categories(categories):
    if not isinstance(categories, dict):
        return {}

    return {
        key: value
        for key, value in categories.items()
        if isinstance(value, int) and value != 0
    }


def save_csv(results):
    prepared_results = []
    for item in results:
        row = dict(item)
        row["categories"] = _nonzero_categories(item.get("categories", {}))
        prepared_results.append(row)

    df = pd.DataFrame(prepared_results)
    df.to_csv("result.csv", index=False)


def save_json(results):
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
def save_md(results):
    with open("result.md", "w", encoding="utf-8") as f:
        f.write("# Отчет по ПДн\n\n")

        for r in results:
            f.write(f"## {r['path']}\n")
            f.write(f"- Категории: {r['categories']}\n")
            f.write(f"- Количество: {r['total_hits']}\n")
            f.write(f"- УЗ: {r['uz']}\n\n")