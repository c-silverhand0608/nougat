import pdfplumber
import re
import json
from typing import List, Dict


def extract_simple_text(pdf_path: str) -> List[str]:
    """增强版PDF文本提取，保留布局结构"""
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # 使用更精确的布局参数
            raw_text = (
                page.extract_text(
                    layout=True,
                    x_tolerance=5,  # 增大水平容差
                    y_tolerance=3,  # 保持垂直精度
                    keep_blank_chars=False,
                )
                or ""
            )
            # 合并换行连字符（保留原始换行符）
            raw_text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", raw_text)
            texts.append(raw_text)
    return texts


def clean_pdf_text(text: str) -> str:
    """保留结构的预处理"""
    # 保留空格、换行符和基本标点
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)  # 处理连字符
    # 移除非文本字符（保留空格、换行和基本标点）
    return re.sub(r"[^\w\s.,!?\-]", "", text).lower()


def get_page_anchors_from_texts(pdf_texts: List[str], num_lines=5) -> List[dict]:
    """智能锚点提取算法"""
    anchors = []
    for i, text in enumerate(pdf_texts):
        # 按保留的换行符分割
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        line_count = len(lines)

        if line_count == 0:
            return {"page": i + 1, "header": "", "footer": ""}

        # 智能识别页眉页脚区域
        header_lines = []
        footer_lines = []

        # 页眉识别（前5行中非页码内容）
        for line in lines[:5]:
            if not re.fullmatch(r"\d+", line):  # 过滤纯数字行
                header_lines.append(line)
                if len(header_lines) >= num_lines:
                    break

        # 页脚识别（后5行中非页码内容）
        for line in reversed(lines[-5:]):
            if not re.fullmatch(r"\d+", line):
                footer_lines.insert(0, line)
                if len(footer_lines) >= num_lines:
                    break

        # 合并有效内容
        header = " ".join(header_lines[:num_lines])
        footer = " ".join(footer_lines[-num_lines:])

        # 去除常见噪声
        header = re.sub(r"\b(arxiv|doi|pp?\.)\b.*", "", header)
        footer = re.sub(r"\b(continued|references)\b.*", "", footer)

        anchors.append(
            {
                "page": i + 1,
                "header": header.strip(),
                "footer": footer.strip(),
                "raw_lines": line_count,  # 调试用原始行数
            }
        )
    return anchors


def get_page_anchors(pdf_path: str) -> List[Dict]:
    """增强版锚点提取流程"""
    pdf_texts = extract_simple_text(pdf_path)
    cleaned_texts = [clean_pdf_text(t) for t in pdf_texts]

    anchors = get_page_anchors_from_texts(cleaned_texts)

    # 后处理：过滤连续重复页眉
    seen_headers = set()
    for anchor in anchors:
        if anchor["header"] in seen_headers:
            anchor["header"] = ""
        else:
            seen_headers.add(anchor["header"])

    anchors_path = pdf_path.replace(".pdf", "_anchors.json")
    with open(anchors_path, "w", encoding="utf-8") as f:
        json.dump(anchors, f, indent=2, ensure_ascii=False)

    return anchors
