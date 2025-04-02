import zipfile
import os
import argparse
from pathlib import Path


def extract_files_from_zip(zip_file_path):
    src_zip = Path(zip_file_path)
    if not src_zip.is_file():
        raise FileNotFoundError(f"zip file not found: {zip_file_path}")

    dest_dir = src_zip.parent / src_zip.stem
    dest_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_file_path, "r") as zf:
        zf.extractall(dest_dir)
        print(f"Extracted all files from {zip_file_path} to {dest_dir}")


def main():
    parser = argparse.ArgumentParser(description="Extract all files from a zip archive")
    parser.add_argument(
        "zip_file_path",
        type=str,
        help="The path to the zip archive from which to extract files",
    )
    args = parser.parse_args()
    extract_files_from_zip(args.zip_file_path)


if __name__ == "__main__":
    main()
