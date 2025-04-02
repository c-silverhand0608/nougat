import fitz
import hashlib
import os
import sys
import json
from PIL import Image
import imagehash


def calculate_phash(image_path):
    """计算抗缩放的感知哈希"""
    try:
        with Image.open(image_path) as img:
            # 统一缩放到64x64并转为灰度
            resized = img.resize((64, 64)).convert("L")
            return str(imagehash.phash(resized))
    except Exception as e:
        print(f"⚠️ 计算pHash失败: {image_path} - {str(e)}")
        return None


def extract_images(pdf_path, output_dir):
    """从PDF提取图片并记录内容哈希"""
    doc = fitz.open(pdf_path)
    image_list = []

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        images = page.get_image_info(xrefs=True)

        for img_info in images:
            xref = img_info["xref"]
            base_image = doc.extract_image(xref)
            img_data = base_image["image"]

            # 计算内容哈希（与HTML图片匹配的关键）
            content_hash = hashlib.md5(img_data).hexdigest()[:8]

            # 保存为PDF提取的图片
            ext = base_image.get("ext", "png").lower()
            filename = f"pdfimg_{content_hash}.{ext}"
            output_path = os.path.join(output_dir, filename)
            with open(output_path, "wb") as f:
                f.write(img_data)

            # 计算坐标
            bbox = img_info["bbox"]
            page_rect = page.rect
            norm_coords = [
                round(bbox[0] / page_rect.width, 4),
                round(1 - bbox[3] / page_rect.height, 4),
                round(bbox[2] / page_rect.width, 4),
                round(1 - bbox[1] / page_rect.height, 4),
            ]

            phash = calculate_phash(output_path)
            image_list.append(
                {
                    "pdf_img_path": filename,
                    "coords": norm_coords,
                    "page": page_num + 1,
                    "phash": phash,  # 新增phash字段
                }
            )

    # 保存映射文件
    mapping_path = os.path.join(output_dir, "image_mapping.json")
    with open(mapping_path, "w") as f:
        json.dump(image_list, f, indent=2)

    print(f"PDF图片提取完成！存储至：{output_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python extract_pdf_images.py <PDF路径> <输出目录>")
        sys.exit(1)

    extract_images(sys.argv[1], sys.argv[2])
