import zipfile
import tarfile
from pathlib import Path
import argparse


def extract_archive(zip_path):
    src_zip = Path(zip_path)
    if not src_zip.is_file():
        raise FileNotFoundError(f"ZIP文件不存在: {zip_path}")

    temp_dir = src_zip.parent / f"_{src_zip.stem}_temp"
    temp_dir.mkdir(exist_ok=True)

    dest_dir = src_zip.parent / src_zip.stem
    dest_dir.mkdir(exist_ok=True)

    try:
        with zipfile.ZipFile(src_zip) as zf:
            zf.extractall(temp_dir)
            print(f"已解压原始ZIP到: {temp_dir}")

        for tmp_file in temp_dir.rglob("*.zip.tmp"):
            if not tarfile.is_tarfile(tmp_file):
                print(f"跳过非tar文件: {tmp_file}")
                continue

            with tarfile.open(tmp_file) as tf:
                tf.extractall(dest_dir)
                print(
                    f"已从 {tmp_file.name} 解压 {len(tf.getnames())} 个文件到 {src_zip.parent}"
                )

    finally:
        for f in temp_dir.glob("*"):
            f.unlink()
        temp_dir.rmdir()
        print("已清理临时文件")


def main():
    parser = argparse.ArgumentParser(description="Extract all files from a zip archive")
    parser.add_argument(
        "zip_file_path",
        type=str,
        help="The path to the zip archive from which to extract files",
    )
    args = parser.parse_args()
    extract_archive(args.zip_file_path)


if __name__ == "__main__":
    main()
