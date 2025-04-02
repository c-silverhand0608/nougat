import pdfplumber
import re
import json
import os
from difflib import SequenceMatcher
from typing import List, Dict
from get_page_anchors import get_page_anchors


# ============== 新增： 构建归一化字符串与索引映射 ==============
def build_norm_map(s: str) -> (str, list):
    """
    返回 (norm_string, index_map):
      norm_string: 仅包含字母+数字的小写序列
      index_map:   norm_string中每个字符在原文s里的下标
    """
    norm_chars = []
    idx_map = []
    for i, ch in enumerate(s):
        if ch.isalnum():  # 只保留字母数字
            norm_chars.append(ch.lower())
            idx_map.append(i)
        # 如果还想保留其它字符, 可自行扩展判断
    return ("".join(norm_chars), idx_map)


def normalize_text_simple(text: str) -> str:
    """
    仅作简单去除非字母数字，转小写的演示。
    (此函数仍保留，以便 minimal 改动, 供别处引用)
    """
    # 仅删除空格：
    text = re.sub(r"\b\d+\.\d+(\.\d+)?\b", "", text)
    return re.sub(r"\s+", "", text).lower()
    # return re.sub(r"[^\w]", "", text).lower()


def find_anchor_pos(full_text: str, anchor: str) -> int:
    """
    通过 '归一化+索引映射' 的方式, 找到 anchor 在 full_text 中的真实下标.
    1) 构建 (norm_full, idx_map_full)
    2) 构建 (norm_anchor, _) 仅仅用于匹配
    3) 在 norm_full 中 find norm_anchor
    4) 如果找到pos, 则 real_pos = idx_map_full[pos]
    5) 若找不到精确匹配, 做滑动窗口模糊匹配 (可选)
    """
    # 1) 构建归一化映射
    norm_full, idx_map_full = build_norm_map(full_text)
    norm_anchor, _ = build_norm_map(anchor)

    with open("norm_full.json", "w") as f:
        json.dump(norm_full, f, indent=2, ensure_ascii=False)

    # 如果 anchor 太长, 截断一下, 避免过长不匹配
    max_len = 25
    if len(norm_anchor) > max_len:
        norm_anchor = norm_anchor[:max_len]

    # 2) 先尝试精确查找
    exact_pos = norm_full.find(norm_anchor)
    # print(f"norm_anchor: {norm_anchor}, exact_pos = {exact_pos}")
    if exact_pos != -1:
        print(f"norm_anchor: {norm_anchor}, exact_pos = {exact_pos}")
        return idx_map_full[exact_pos]
    # else:
    #     return -1

    # 3) 精确找不到, 做简易模糊匹配(滑动窗口+SequenceMatcher)
    #    这里为了最小改动, 直接与 anchor 做 ratio
    best_score, best_pos = 0, -1
    window_size = min(len(norm_anchor) * 2, 500)
    step = max(1, window_size // 2)
    for i in range(0, len(norm_full) - window_size + 1, step):
        chunk = norm_full[i : i + window_size]
        score = SequenceMatcher(None, chunk, norm_anchor).ratio()
        if score > best_score:
            best_score = score
            best_pos = i

    # 阈值判断
    if best_score > 0.75 and best_pos != -1:
        # best_pos 是 norm_full 中的起点
        return idx_map_full[best_pos]

    return -1


def split_mmd(full_mmd: str, anchors: List[Dict]) -> List[str]:
    """
    改动: 使用 find_anchor_pos 返回的原文下标, 在 full_mmd 中分割
    """
    page_breaks = [0]

    # 第一页
    pos = find_anchor_pos(full_mmd, anchors[0]["header"])
    if pos != -1:
        page_breaks.append(pos)
    else:
        # 回退
        page_breaks.append(0)

    # 逐页
    for i in range(1, len(anchors)):
        boundary = anchors[i]["header"]
        pos = find_anchor_pos(full_mmd, boundary)
        if pos == -1:
            pos = find_anchor_pos(full_mmd, anchors[i]["header"])
            if pos == -1:
                # 估算
                pos = page_breaks[-1] + len(full_mmd) // (len(anchors) + 1)
        page_breaks.append(pos)

    page_breaks.append(len(full_mmd))

    # 生成输出
    pages = []
    for start, end in zip(page_breaks, page_breaks[1:]):
        if end < start:  # 防止异常倒序
            end = start
        segment = full_mmd[start:end].strip()
        if segment:  # 过滤空段
            pages.append(segment)

    return pages


# ==================== 端到端测试 ====================


def main():
    MMD_FILE = "/home/ninziwei/lyj/nougat/__test_1/html/2303.00058/2303.00058.mmd"
    with open(MMD_FILE, "r", encoding="utf-8") as f:
        MMD_CONTENT = f.read()

    # Step 1: 提取PDF锚点
    ANCHORS_FILE = (
        "/home/ninziwei/lyj/nougat/__test_1/src/2303.00058/2303.00058_anchors.json"
    )
    # if os.path.exists(ANCHORS_FILE):
    #     with open(ANCHORS_FILE, "r", encoding="utf-8") as f:
    #         anchors = json.load(f)
    # else:
    anchors = get_page_anchors(
        "/home/ninziwei/lyj/nougat/__test_1/src/2303.00058/2303.00058.pdf"
    )

    # Step 2: 分页MMD
    mmd_pages = split_mmd(MMD_CONTENT, anchors)

    # 验证分页结果
    # print("\n=== MMD分页结果 ===")
    # for i, page in enumerate(mmd_pages):
    #     start_preview = page[:30].replace("\n", " ")
    #     end_preview = page[-30:].replace("\n", " ")
    #     print(f"Page {i+1}:")
    #     print(f"  Start: {start_preview}...")
    #     print(f"  End: {end_preview}...")
    #     print(f"  Length: {len(page)} chars\n")
    with open("pages.json", "w") as f:
        json.dump(mmd_pages, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
