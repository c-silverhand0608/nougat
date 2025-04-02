import zipfile
from pathlib import Path
import tarfile


def is_zip_valid(zip_file_path):
    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_file:
            bad_file = zip_file.testzip()
            if bad_file is not None:
                print(f"ZIP 文件损坏，损坏的文件是: {bad_file}")
                return False
            return True
    except zipfile.BadZipFile as e:
        print(f"ZIP 文件损坏: {e}")

    return False


# def extract_usual_zip(zip_file_path):
#     src_zip = Path(zip_file_path)
#     if not src_zip.is_file():
#         raise FileNotFoundError(f"zip file not found: {zip_file_path}")

#     dest_dir = src_zip.parent / src_zip.stem
#     dest_dir.mkdir(exist_ok=True)

#     with zipfile.ZipFile(zip_file_path, "r") as zf:
#         zf.extractall(dest_dir)
#         print(f"Extracted all files from {zip_file_path} to {dest_dir}")


def extract_zip(zip_file_path):
    src_zip = Path(zip_file_path)
    if not src_zip.is_file():
        raise FileNotFoundError(f"ZIP文件不存在: {zip_file_path}")

    temp_dir = src_zip.parent / f"_{src_zip.stem}_temp"
    temp_dir.mkdir(exist_ok=True)

    dest_dir = src_zip.parent / src_zip.stem
    dest_dir.mkdir(exist_ok=True)

    try:
        with zipfile.ZipFile(src_zip) as zf:
            zf.extractall(temp_dir)
            print(f"已解压原始ZIP到: {temp_dir}")

        # if there is no .tmp, then it's done
        if not any(temp_dir.rglob("*.zip.tmp")):
            for f in temp_dir.glob("*"):
                f.rename(dest_dir / f.name)
            print(
                f"已从 {src_zip} 解压 {len(list(dest_dir.glob('*')))} 个文件到 {dest_dir}，正常zip文件"
            )
            return

        for tmp_file in temp_dir.rglob("*.zip.tmp"):
            if not tarfile.is_tarfile(tmp_file):
                print(f"跳过非tar文件: {tmp_file}")
                continue

            with tarfile.open(tmp_file) as tf:
                tf.extractall(dest_dir)
                print(
                    f"已从 {tmp_file.name} 解压 {len(tf.getnames())} 个文件到 {src_zip.parent}，tar文件"
                )
    except Exception as e:
        print(f"解压ZIP文件时出错: {e}")

    finally:
        for f in temp_dir.glob("*"):
            f.unlink()
        temp_dir.rmdir()
        print("已清理临时文件")
