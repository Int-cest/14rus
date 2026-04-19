from pathlib import Path

from config import PATH_DATA
from pipeline import Pipeline
from report import make_result, save_csv


def main() -> None:
	input_path = Path(PATH_DATA)
	if not input_path.exists():
		raise FileNotFoundError(f"Папка не найдена: {input_path}")

	results = Pipeline().run(str(input_path))

	save_csv(results)
	make_result(results)

if __name__ == "__main__":
	main()
