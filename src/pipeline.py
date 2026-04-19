import logging
import time
from pathlib import Path

from parcer import ParserFactory
from detector import Detector
from classifier import Classifier

logger = logging.getLogger("parcer")


class Pipeline:

    def __init__(self, debug: bool = False):
        self.parser = ParserFactory()
        self.detector = Detector(debug=debug)
        self.classifier = Classifier()
        self.debug = debug

    def run(self, root_path: str):
        started_at = time.perf_counter()
        logger.info("[Pipeline] Start root=%s", root_path)

        parsed_files = self.parser.scan_directory(root_path)

        results = []
        total = len(parsed_files)

        # ---- NEW: global error stats ----
        stats = {
            "total_hits": 0,
            "weak_passages": 0,
            "ocr_noise_files": 0
        }

        for index, item in enumerate(parsed_files, start=1):
            text = item.get("content", "")
            path = item.get("path")

            # ---------------- DETECT ----------------
            detect_result = self.detector.detect(text)
            if isinstance(detect_result, tuple):
                raw_detections = detect_result[0] if len(detect_result) > 0 else {}
                trace = detect_result[1] if len(detect_result) > 1 else []
            else:
                raw_detections = detect_result
                trace = []

            if not isinstance(raw_detections, dict):
                logger.warning("[Pipeline] Unexpected detector output type: %s", type(raw_detections).__name__)
                raw_detections = {}

            detections = {}
            for key in ("обычные", "государственные", "платёжные", "биометрические", "специальные"):
                value = raw_detections.get(key, 0)
                if isinstance(value, int):
                    detections[key] = value
                elif isinstance(value, (list, tuple, set, dict)):
                    detections[key] = len(value)
                else:
                    detections[key] = 0

            total_count = sum(detections.values())
            uz = self.classifier.classify(detections)

            # ---------------- ANALYSIS ----------------
            if self.debug:
                # слабые сигналы
                if total_count > 0 and total_count <= 2:
                    stats["weak_passages"] += 1

                # OCR noise heuristic
                if len(text) > 0 and text.count(" ") / len(text) < 0.08:
                    stats["ocr_noise_files"] += 1

                stats["total_hits"] += total_count

            results.append({
                "path": path,
                "categories": detections,
                "uz": uz,
                "total_hits": total_count,
                "ext": Path(path).suffix,
                # --- NEW DEBUG INFO ---
                "trace": trace if self.debug else None
            })

            if index % 50 == 0 or index == total:
                elapsed = time.perf_counter() - started_at
                rate = index / elapsed if elapsed else 0

                logger.info(
                    "[Pipeline] %s/%s | %.1f sec | %.2f files/sec",
                    index, total, elapsed, rate
                )

        elapsed = time.perf_counter() - started_at

        # -------- FINAL DEBUG REPORT --------
        if self.debug:
            logger.info("========== DEBUG SUMMARY ==========")
            logger.info("Total signal hits: %s", stats["total_hits"])
            logger.info("Weak passages: %s", stats["weak_passages"])
            logger.info("Possible OCR noise files: %s", stats["ocr_noise_files"])
            logger.info("===================================")

        logger.info("[Pipeline] Done in %.1fs", elapsed)

        return results