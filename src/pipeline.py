import logging
import time
from pathlib import Path
from parcer import ParserFactory
from detector import Detector
from classifier import Classifier


logger = logging.getLogger("parcer")

class Pipeline:
    def __init__(self):
        self.parser = ParserFactory()
        self.detector = Detector()
        self.classifier = Classifier()

    def run(self, root_path: str):
        started_at = time.perf_counter()
        logger.info("[Pipeline] Старт обработки root_path=%s", root_path)
        parsed_files = self.parser.scan_directory(root_path)

        results = []
        total = len(parsed_files)

        for index, item in enumerate(parsed_files, start=1):
            text = item.get("content", "")
            path = item.get("path")

            # --- detection ---
            detections = self.detector.detect(text)

            # --- count ---
            total_count = sum(detections.values())

            # --- classification ---
            uz = self.classifier.classify(detections)
            categories = [k for k, v in detections.items() if v > 0]

            results.append({
                "path": path,
                "categories": categories,
                "count": total_count,
                "uz": uz,
                "format": Path(path).suffix
            })

            if index % 50 == 0 or index == total:
                time_elapsed = time.perf_counter() - started_at
                rate = index / time_elapsed if time_elapsed > 0 else 0.0
                logger.info(
                    "[Pipeline] Прогресс детекции: processed=%s/%s, elapsed=%.1fs, rate=%.2f files/s",
                    index,
                    total,
                    time_elapsed,
                    rate,
                )

        time_elapsed = time.perf_counter() - started_at
        logger.info("[Pipeline] Завершено: processed=%s, elapsed=%.1fs", len(results), time_elapsed)

        return results