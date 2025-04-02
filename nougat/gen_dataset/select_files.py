import os
import shutil
import random
from unzip import extract_zip


def is_zip_wanted(zip_path):
    pdf_path = zip_path.replace(".zip", ".pdf")
    if not os.path.exists(pdf_path):
        return False

    target_dir = zip_path.replace(".zip", "")
    if os.path.exists(target_dir):
        for root, _, files in os.walk(target_dir):
            for file in files:
                # found files like main-*.tex
                if file.endswith(".tex") and file.startswith("main-"):
                    return False

    extract_zip(zip_path)

    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".pdf"):
                shutil.rmtree(target_dir)
                return False
    shutil.rmtree(target_dir)

    return True


def find_all_zips(latex_pdf_root):
    zip_files = []

    for root, _, files in os.walk(latex_pdf_root):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".zip"):
                zip_files.append(file_path)

    random.shuffle(zip_files)
    return zip_files
