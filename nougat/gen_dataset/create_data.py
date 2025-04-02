import os
import shutil
from pathlib import Path
from unzip import extract_zip
from convert_tex_to_html import convert_tex_to_html
from extract_pdf_images import extract_images
from inject_coords import inject_coordinates

# target_root = "/data1/nzw/latex_pdf/generated_dataset"
target_root = "/home/ninziwei/lyj/nougat/__test_new"


def walk_and_create(zip_file):
    pdf_file = zip_file.replace(".zip", ".pdf")

    # target dirs and files
    target_src_dir = os.path.join(target_root, "src")
    target_pdf_dir = os.path.join(target_src_dir, Path(zip_file).stem)
    target_pdf_file = os.path.join(target_pdf_dir, Path(pdf_file).name)
    target_zip_file = os.path.join(target_src_dir, Path(zip_file).name)

    # copy pdf&zip and unzip
    if not os.path.exists(target_zip_file):
        shutil.copy(zip_file, target_zip_file)
    extract_zip(target_zip_file)
    if not os.path.exists(target_pdf_file):
        shutil.copy(pdf_file, target_pdf_file)
    print(f"unzip {target_zip_file} done")

    # get html
    target_html_dir = target_pdf_dir.replace("src", "html")
    os.makedirs(target_html_dir, exist_ok=True)
    try:
        # convert tex to html
        if convert_tex_to_html(target_pdf_dir, target_html_dir):
            print(f"convert {target_pdf_file} to html done")
            # extract names
            # target_name_dir = os.path.join(target_pdf_dir, "nametxt")
            # extract_names_from_tex(target_pdf_dir, target_name_dir)
            # print(f"extract names from {target_pdf_file} done")

            # extract images
            target_img_dir = os.path.join(target_pdf_dir, "extracted_images")
            extract_images(target_pdf_file, target_img_dir)
            print(f"extract images from {target_pdf_file} done")

            # inject coordinates
            target_img_mapping = os.path.join(target_img_dir, "image_mapping.json")
            target_html_file = os.path.join(
                target_html_dir, Path(pdf_file).stem + ".html"
            )
            inject_coordinates(target_html_file, target_img_mapping, target_html_file)
            print(f"inject coordinates to {target_html_file} done")

            return True
    except Exception as e:
        print(f"convert {target_pdf_file} to html failed: {e}")

    return False


# walk_and_create("/home/ninziwei/lyj/nougat/__test_new/src/2402.00041.zip")
walk_and_create("/home/ninziwei/lyj/nougat/__test_new/src/2303.00058.zip")
# walk_and_create("/home/ninziwei/lyj/nougat/__test_new/src/2303.00065.zip")

"""
python extract_pdf_images.py \
/home/ninziwei/lyj/nougat/__test/2402.00041.pdf \
/home/ninziwei/lyj/nougat/__test/2402.00041/extracted_images

python inject_coords.py \
/home/ninziwei/lyj/nougat/__test/2402.00041/html/2402.00041.html \
/home/ninziwei/lyj/nougat/__test/2402.00041/extracted_images/image_mapping.json \
/home/ninziwei/lyj/nougat/__test/2402.00041/html/2402.00041_with_coords.html 

python extract_name_from_tex.py \
/home/ninziwei/lyj/nougat/__test/2402.00041 \
/home/ninziwei/lyj/nougat/__test/2402.00041/nametxt
"""
