from __future__ import annotations

from pathlib import Path
import urllib.request
import zipfile


MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"

DATA_DIR = Path("/datasets/raw_data")
ZIP_PATH = DATA_DIR / "ml-latest-small.zip"

REQUIRED = {
    "movies.csv": "ml-latest-small/movies.csv",
    "ratings.csv": "ml-latest-small/ratings.csv",
}


def download_if_needed() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if ZIP_PATH.exists() and ZIP_PATH.stat().st_size > 0:
        print(f"Archive already present: {ZIP_PATH}")
        return

    print(f"Downloading MovieLens dataset to {ZIP_PATH} ...")
    urllib.request.urlretrieve(MOVIELENS_URL, ZIP_PATH)
    print("Download complete.")


def extract_required_files() -> None:
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Missing archive: {ZIP_PATH}")

    with zipfile.ZipFile(ZIP_PATH) as z:
        for out_name, in_zip_path in REQUIRED.items():
            out_path = DATA_DIR / out_name
            if out_path.exists() and out_path.stat().st_size > 0:
                print(f"{out_name} already exists: {out_path}")
                continue

            print(f"Extracting {in_zip_path} -> {out_path}")
            with z.open(in_zip_path) as src, open(out_path, "wb") as dst:
                dst.write(src.read())

    print("Dataset ready:")
    for out_name in REQUIRED.keys():
        p = DATA_DIR / out_name
        print(f" - {p} ({p.stat().st_size} bytes)")


def main() -> None:
    download_if_needed()
    extract_required_files()


if __name__ == "__main__":
    main()
