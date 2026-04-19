import pandas as pd
import csv
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from config import PATH_DATA


MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def _nonzero_categories(categories):
    if not isinstance(categories, dict):
        return {}

    return {
        key: value
        for key, value in categories.items()
        if isinstance(value, int) and value != 0
    }


def _format_time(ts: float) -> str:
    dt = datetime.fromtimestamp(ts)
    return f"{MONTHS[dt.month - 1]} {dt.day:02d} {dt.strftime('%H:%M')}"


def _candidate_paths(search_roots: list[Path], relative_name: str) -> list[Path]:
    raw = relative_name.strip()
    decoded = unquote(raw)

    variants = {
        raw,
        raw.replace("\\", "/"),
        decoded,
        decoded.replace("\\", "/"),
    }

    candidates: list[Path] = []
    for root in search_roots:
        for rel in variants:
            candidates.append(root / rel)

    return candidates


def _extract_filename(relative_name: str) -> str:
    normalized = unquote(relative_name.strip()).replace("\\", "/")
    return normalized.rsplit("/", 1)[-1]


def _unique_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()

    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)

    return unique


def save_csv(results):
    prepared_results = []
    for item in results:
        row = dict(item)
        row["categories"] = _nonzero_categories(item.get("categories", {}))
        prepared_results.append(row)

    df = pd.DataFrame(prepared_results)
    df.to_csv("report.csv", index=False)


def make_result(results):
    project_root = Path(__file__).resolve().parent.parent

    configured_root = Path(PATH_DATA)
    if not configured_root.is_absolute():
        configured_root = (project_root / configured_root).resolve()

    search_roots = _unique_paths(
        [
            configured_root,
            project_root / "datasets" / "share",
            project_root / "datasets" / "data",
            project_root / "datasets" / "test",
            project_root,
        ]
    )

    result_rows: list[dict[str, str]] = []

    for item in results:
        total_hits = int(item.get("total_hits", item.get("count", 0)) or 0)
        if total_hits <= 0:
            continue

        name = str(item.get("path", item.get("name", ""))).strip()
        if not name:
            continue

        file_path = None
        for cand in _candidate_paths(search_roots, name):
            if cand.exists() and cand.is_file():
                file_path = cand
                break

        if file_path is None:
            continue

        filename = _extract_filename(name)
        if not filename:
            continue

        stat = file_path.stat()
        result_rows.append(
            {
                "size": str(stat.st_size),
                "time": _format_time(stat.st_mtime),
                "name": filename,
            }
        )

    result_rows.sort(key=lambda row: row["name"])

    with open("result.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["size", "time", "name"])
        writer.writeheader()
        writer.writerows(result_rows)