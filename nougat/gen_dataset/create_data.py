import os
import shutil
from pathlib import Path
from unzip import extract_files_from_tar_zip
from convert_tex_to_html import convert_tex_to_html
from bs4 import BeautifulSoup
from nougat.dataset.patches.bib_fixer import fix_bibliography
from nougat.dataset.patches.cite_fixer import fix_citations

# target_root = "/data1/nzw/latex_pdf/generated_dataset"
target_root = "/home/ninziwei/lyj/nougat/__test_1"


def check_bib_and_fix(html_file, bbl_dir):
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # if there is no ltx_missing_citation, then no need to fix
    if not soup.find_all("span", {"class": "ltx_missing_citation"}):
        print(f"no missing citation in {html_file}")
        return

    # find .bbl file
    for root, _, files in os.walk(bbl_dir):
        for file in files:
            if file.endswith(".bbl"):
                # tex_file is used to check if it matches the .bbl only
                tex_file = Path(file).stem + ".tex"
                if not tex_file in files:
                    continue

                bbl_file = os.path.join(root, file)

                print(f"--- start fixing {html_file} using {bbl_file} ---")
                fix_bibliography(html_file, bbl_file)
                fix_citations(html_file, bbl_file)
                print(f"修复引用: {html_file} -> {bbl_file}")
                break


def walk_and_create(zip_file):
    pdf_file = zip_file.replace(".zip", ".pdf")

    # target dirs and files
    target_src_parent_dir = os.path.join(target_root, "src")
    target_pdf_dir = os.path.join(target_src_parent_dir, Path(zip_file).stem)
    target_pdf_file = os.path.join(target_pdf_dir, Path(pdf_file).name)
    target_zip_file = os.path.join(target_src_parent_dir, Path(zip_file).name)

    # copy pdf&zip and unzip
    if not os.path.exists(target_zip_file):
        shutil.copy(zip_file, target_zip_file)
    extract_files_from_tar_zip(target_zip_file)
    if not os.path.exists(target_pdf_file):
        shutil.copy(pdf_file, target_pdf_file)
    print(f"unzip {target_zip_file} done")

    # get html
    target_html_dir = target_pdf_dir.replace("src", "html")
    os.makedirs(target_html_dir, exist_ok=True)
    try:
        # convert tex to html
        # if convert_tex_to_html(target_pdf_dir, target_html_dir):
        #     target_html_file = os.path.join(
        #         target_html_dir, Path(pdf_file).stem + ".html"
        #     )
        #     # check bib and fix
        #     check_bib_and_fix(target_html_file, target_pdf_dir)

        #     print(f"convert {target_pdf_file} to html done")
        #     return True
        target_html_file = os.path.join(target_html_dir, Path(pdf_file).stem + ".html")
        check_bib_and_fix(target_html_file, target_pdf_dir)
    except Exception as e:
        print(f"convert {target_pdf_file} to html failed: {e}")

    return False


# walk_and_create("/home/ninziwei/lyj/nougat/__test_new/src/2402.00041.zip")
walk_and_create("/home/ninziwei/lyj/nougat/__test_1/src/2303.00058.zip")
# walk_and_create("/home/ninziwei/lyj/nougat/__test_new/src/2303.00065.zip")
