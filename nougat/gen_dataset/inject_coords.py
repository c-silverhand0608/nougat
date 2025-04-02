import sys
import json
import os
import cv2
import numpy as np
from bs4 import BeautifulSoup
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


def find_best_match(target_hash, phash_db, threshold=5):
    """寻找最相似的哈希匹配"""
    if not target_hash:
        return None

    min_distance = float("inf")
    best_match = None
    for pdf_hash, pdf_data in phash_db.items():
        # 计算汉明距离
        distance = bin(int(target_hash, 16) ^ int(pdf_hash, 16)).count("1")
        if distance < min_distance and distance <= threshold:
            min_distance = distance
            best_match = pdf_data

    return best_match if best_match else None


# --- 新增：ORB特征计算函数 ---
def compute_orb_descriptor(image_path):
    """
    使用 ORB 提取图像关键点和描述子
    返回 (kp, des)
    """
    if not os.path.exists(image_path):
        return None, None
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, None
    orb = cv2.ORB_create()
    kp, des = orb.detectAndCompute(img, None)
    return kp, des


# --- 新增：ORB特征匹配评分 ---
def orb_similarity(kp1, des1, kp2, des2, match_threshold=40):
    """
    用 BFMatcher 进行描述子匹配，并返回“足够好”的匹配数量
    match_threshold 可以视情况调整
    """
    if des1 is None or des2 is None:
        return 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    # 按距离升序
    matches = sorted(matches, key=lambda x: x.distance)
    # 统计“距离小于 match_threshold”的匹配数
    good = [m for m in matches if m.distance < match_threshold]
    return len(good)


def inject_coordinates(html_path, mapping_path, output_path):
    # 加载PDF图片的感知哈希数据库
    with open(mapping_path) as f:
        pdf_images = json.load(f)

    # 预处理PDF图片的pHash
    phash_db = {}
    for img in pdf_images:
        pdf_img_path = os.path.join(os.path.dirname(mapping_path), img["pdf_img_path"])
        phash = calculate_phash(pdf_img_path)
        if phash:
            phash_db[phash] = img
            img["phash"] = phash  # 记录用于调试

    print(f"🛠️ 已加载 {len(phash_db)} 个PDF图片的感知哈希")

    # --- 新增：预计算所有 PDF 图片的 ORB 特征描述子，供兜底匹配使用 ---
    orb_db = {}
    for pdf_item in pdf_images:
        pdf_full_path = os.path.join(
            os.path.dirname(mapping_path), pdf_item["pdf_img_path"]
        )
        kp_pdf, des_pdf = compute_orb_descriptor(pdf_full_path)
        # 以 PDF 文件的绝对路径为key，存储 (kp, des, 原pdf_item)
        orb_db[pdf_full_path] = (kp_pdf, des_pdf, pdf_item)

    # 解析HTML
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # 遍历所有图片
    total_matched = 0
    for img_tag in soup.find_all("img"):
        src = img_tag.get("src", "")
        print(f"\n🔍 处理图片: {src}")

        # 使用html目录下的x1.png, x2.png...进行匹配
        html_img_path = os.path.join(os.path.dirname(html_path), src)  # HTML同级目录

        # 计算感知哈希
        current_phash = calculate_phash(html_img_path)
        if not current_phash:
            print("⚠️ pHash计算失败，尝试ORB匹配...")
            match = None
        else:
            # 寻找最佳pHash匹配
            match = find_best_match(current_phash, phash_db)

        if match:
            # --- pHash 匹配成功 ---
            print(
                f"✅ 匹配成功: {os.path.basename(html_img_path)} → {match['pdf_img_path']}"
            )
            print(
                f"  汉明距离: {bin(int(current_phash,16) ^ int(match['phash'],16)).count('1')}"
            )
        else:
            # --- pHash 匹配失败，尝试 ORB ---
            kp_html, des_html = compute_orb_descriptor(html_img_path)
            if des_html is None:
                print("⚠️ ORB特征无法读取，放弃匹配。")
                continue
            best_score = 0
            best_pdf_item = None
            for pdf_path, (kp_pdf, des_pdf, pdf_item) in orb_db.items():
                score = orb_similarity(
                    kp_html, des_html, kp_pdf, des_pdf, match_threshold=40
                )
                if score > best_score:
                    best_score = score
                    best_pdf_item = pdf_item

            # 这里可自行调整阈值，如 score>20 即视为匹配成功
            if best_score > 20 and best_pdf_item is not None:
                match = best_pdf_item
                print(
                    f"✅ ORB匹配成功: {os.path.basename(html_img_path)} → {match['pdf_img_path']} (score={best_score})"
                )
            else:
                print(f"❌ 未找到匹配项 (ORB score={best_score})")
                match = None

        # 若最终 match 不为 None，就注入坐标
        if match:
            total_matched += 1
            # 查找父级 figure 或 span，且必须包含类名 ltx_figure
            figure = img_tag.find_parent(
                lambda tag: tag.name in ["figure", "span"]
                and "ltx_figure" in tag.get("class", [])
            )
            if figure:
                coords_str = ",".join(f"{c:.4f}" for c in match["coords"])
                figure["data-coords"] = coords_str
                figure["data-source"] = match["pdf_img_path"]
                print(f"  注入坐标: {coords_str}")
            else:
                print("⚠️ 未找到父级figure标签")

    # 保存结果
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"\n📊 最终匹配结果: {total_matched}/{len(soup.find_all('img'))}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("用法: python inject_coords.py <HTML输入> <映射JSON> <HTML输出>")
        sys.exit(1)

    inject_coordinates(
        html_path=sys.argv[1],
        mapping_path=sys.argv[2],
        output_path=sys.argv[3],
    )
