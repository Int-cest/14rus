from pathlib import Path
from parcer import ParserFactory
from detector import Detector
from classifier import Classifier

class Pipeline:
    def __init__(self):
        self.parser = ParserFactory()
        self.detector = Detector()
        self.classifier = Classifier()

    def run(self, root_path: str):
        parsed_files = self.parser.scan_directory(root_path)

        results = []

        for item in parsed_files:
            text = item.get("content", "")
            path = item.get("path")

            # --- detection ---
            detections = self.detector.detect(text)

            # --- count ---
            total_count = sum(len(v) for v in detections.values())

            # --- classification ---
            uz = self.classifier.classify(detections)

            results.append({
                "path": path,
                "categories": list(detections.keys()),
                "count": total_count,
                "uz": uz,
                "format": Path(path).suffix
            })

        return results