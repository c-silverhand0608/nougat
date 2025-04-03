import zipfile
import tarfile
from pathlib import Path
import argparse


def extract_files_from_zip(zip_file_path):
    """
    Extract all files from a common zip archive.
    Args:
        zip_file_path (str): The path to the zip archive from which to extract files.
    """
    # 检查文件是否存在
    src_zip = Path(zip_file_path)
    if not src_zip.is_file():
        raise FileNotFoundError(f"zip file not found: {zip_file_path}")

    # 创建目标目录
    dest_dir = src_zip.parent / src_zip.stem
    dest_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_file_path, "r") as zf:
        zf.extractall(dest_dir)
        print(f"Extracted all files from {zip_file_path} to {dest_dir}")


def extract_files_from_tar_zip(zip_file_path):
    """
    Extract all files from an abnormal zip archive in our specific format.
    **Please ignore this function if you are not using our specific zip format.**
    Args:
        zip_file_path (str): The path to the zip archive from which to extract files.
    """

    # 检查文件是否存在
    src_zip = Path(zip_file_path)
    if not src_zip.is_file():
        raise FileNotFoundError(f"ZIP文件不存在: {zip_file_path}")

    # 创建临时目录
    temp_dir = src_zip.parent / f"_{src_zip.stem}_temp"
    temp_dir.mkdir(exist_ok=True)

    # 创建目标目录
    dest_dir = src_zip.parent / src_zip.stem
    dest_dir.mkdir(exist_ok=True)

    # 解压缩ZIP文件到临时目录
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
    extract_files_from_tar_zip(args.zip_file_path)


if __name__ == "__main__":
    main()
