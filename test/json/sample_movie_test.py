from datetime import datetime
import json
from pathlib import Path
import random

random.seed(42)

MOVIE_TEST_DATA_DIR = Path(__file__).parent / "movie_test_v1.3.json"

SAMPLE_SIZE = 20
TODAY_DATETIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SAMPLED_MOVIE_TEST_DATA_DIR = Path(__file__).parent / f"sampled_movie_test_data_{TODAY_DATETIME}.json"


def load_movie_data(file_path: Path) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def main():
    movie_data = load_movie_data(MOVIE_TEST_DATA_DIR)
    sampled_data = random.sample(movie_data, SAMPLE_SIZE)
    with open(SAMPLED_MOVIE_TEST_DATA_DIR, "w", encoding="utf-8") as file:
        json.dump(sampled_data, file, ensure_ascii=False, indent=4)
    print(f"Sampled {SAMPLE_SIZE} movie test data entries to {SAMPLED_MOVIE_TEST_DATA_DIR}")


if __name__ == "__main__":
    main()
