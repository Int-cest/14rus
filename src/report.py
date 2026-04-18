import pandas as pd
import json

def save_csv(results):
    df = pd.DataFrame(results)
    df.to_csv("report.csv", index=False)


def save_json(results):
    with open("report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
def save_md(results):
    with open("report.md", "w", encoding="utf-8") as f:
        f.write("# Отчет по ПДн\n\n")

        for r in results:
            f.write(f"## {r['path']}\n")
            f.write(f"- Категории: {r['categories']}\n")
            f.write(f"- Количество: {r['count']}\n")
            f.write(f"- УЗ: {r['uz']}\n\n")