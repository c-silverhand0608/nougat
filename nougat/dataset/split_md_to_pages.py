"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

import os
import re
import json
import pypdf
import argparse

import jieba
import random
import numpy as np

from typing import Dict, List, Tuple

from string_matcher import get_char_match_score
from rasterize import rasterize_paper


def debug(*args, **kwargs):
    """
    Debug function to print messages with a specific format.
    """
    # Uncomment the next line to enable debug printing
    # print("DEBUG:", *args, **kwargs)
    pass


def get_doc_text(doc):
    """
    先清洗掉所有 [TABLE] 和 [ENDTABLE] 之间，
        [ALGORITHM] 和 [ENDALGORITHM] 之间,
        [FOOTNOTE] 和 [ENDFOOTNOTE] 之间,
        [LISTING] 和 [ENDLISTING] 之间
    的所有文本
    然后清洗掉[FIGURE:xxxx] 和 [ENDFIGURE] 标签及其之间的所有文本，xxxx表示图表的编号，可能是不同的字符
    从 doc 中提取出所有 [TEXT] 和 [ENDTEXT] 之间的文本并用 '\n' 将其拼接成一个长文本
    doc 中有多组 [TEXT] 和 [ENDTEXT]，请提取每一对 [TEXT] 和 [ENDTEXT] 之间的文本
    """
    # 使用正则表达式找到所有 [TEXT] 和 [ENDTEXT] 之间的内容
    text_blocks = re.finditer(r"\[TEXT\](.*?)\[ENDTEXT\]", doc, re.DOTALL)

    # 将所有找到的文本块用换行符连接
    doc_text = "\n".join(block.group(1).strip() for block in text_blocks)

    # 如果没有找到任何 [TEXT] 标记，则使用整个文档
    if not doc_text:
        doc_text = doc

    return doc_text


def squeeze_text(text: str) -> str:
    return (
        text.replace("\n", "").replace("\t", "").replace("\xa0", " ").replace(" ", "")
    )


# 定义一个函数去掉公式中的转义符
def decode_formula(text):
    # 简单替换一些常见的LaTeX公式符号
    text = re.sub(r"\\cdot", "·", text)
    text = re.sub(r"\\sum_\{([^}]*)\}", "Σ", text)
    text = re.sub(r"\\\(|\\\)", "", text)
    text = re.sub(r"\{|\}", "", text)
    text = re.sub(r"\\", "", text)
    text = re.sub(r"\^(-?[0-9]+)", "\\1", text)
    return text


def build_inverted_index(lines: List[str]) -> Dict[str, List[int]]:
    """
    构建倒排索引，返回一个字典，键为单词，值为该单词在行数组中的索引列表
    """
    inverted_index = {}
    for i, line in enumerate(lines):
        words = jieba.lcut(line)
        words = [word.strip() for word in words if len(word.strip()) > 1]
        words = list(set(words))
        for word in words:
            inverted_index.setdefault(word, []).append(i)
    return inverted_index


def split_markdown(
    doc,
    pdf,
    figure_info,
) -> Tuple[List[str], Dict]:
    """
    Split a PDF document into Markdown paragraphs.

    Args:
        doc (str): latex 转 html 再转 markdown 后 md 文本内容.
        pdf (pypdf.PdfReader): 用 pypdf 读取 pdf 文件的结果.
        figure_info (Optional[List[Dict]]): 图表信息，每个字典指定一个图表的信息，包括标题、页码和边界框.

    Returns:
        doc_lines_by_pages: 每一页的行数组
        coinside_pages: 两页重合的页码对
        bad_pages: 两页冲突的页码对
    """
    from itertools import chain

    # 用正则表达式从 doc 中提取出所有 [TEXT] 和 [ENDTEXT] 之间的文本
    doc_text = get_doc_text(doc).lower()

    doc_lines = doc_text.split("\n")
    doc_lines = [line.strip() for line in doc_lines if line.strip()]

    # 用 decode_formula 函数去掉 line 中所有公式的转义符
    doc_lines = [decode_formula(line) for line in doc_lines]

    # 提取图表标题
    caption_lines = []
    if "figures" in figure_info:
        caption_lines = [item.get("caption", "") for item in figure_info["figures"]]
        caption_lines = [decode_formula(line) for line in caption_lines if line]

    # 对 doc_lines 中的每一行分词后构建从 word 到行号的倒排索引
    doc_inverted_index = build_inverted_index(doc_lines)
    caption_inverted_index = build_inverted_index(caption_lines)

    strip_doc_text = squeeze_text(doc_text)
    strip_doc_lines = [squeeze_text(line) for line in doc_lines]
    strip_caption_lines = [squeeze_text(line) for line in caption_lines]
    strip_caption_text = "".join(strip_caption_lines)

    # out_path = "/home/ninziwei/projects/nougat_ocr/nougat/dataset/test/out"
    # with open(f"{out_path}/strip_doc_lines.txt", "w", encoding="utf-8") as f:
    #     f.write("\n".join(strip_doc_lines))

    # 获取干净的 pdf 中的纯文本
    lines_of_pages = []

    for page in pdf.pages:
        page_text = page.extract_text()
        page_lines = page_text.split("\n")
        page_lines = [line.strip().lower() for line in page_lines if line.strip()]
        strip_page_lines = [squeeze_text(line) for line in page_lines]
        valid_lines = []

        for i, (line, strip_line) in enumerate(zip(page_lines, strip_page_lines)):
            # 如果行长度太短，跳过
            if len(strip_line) <= 3:
                continue

            if "must be allocated to distinct" in line:
                debug(130, line)
                debug(131, strip_line)
                debug(strip_line in strip_doc_text)

            # 如果行长度大于20，则可以用完美匹配的方式直接判断是否有效
            if len(strip_line) > 20:
                if strip_line in strip_doc_text:
                    valid_lines.append(line)
                    continue
                # elif strip_line in strip_caption_text:
                #     valid_lines.append(line)
                #     continue

            tmp_line = "".join(re.split(r"-|_| ", line))
            if (
                line.isalpha()
                or line.isdigit()
                or tmp_line.isalpha()
                or tmp_line.isdigit()
            ):
                continue

            words = jieba.lcut(line)
            words = [word.strip() for word in words if len(word.strip()) > 1]

            # 如果分词后的单词数量不足5个，使用所有单词
            if len(words) > 5:
                words = random.sample(words, 5)

            # 获取候选行索引
            candid_doc_line_idxes = set(
                chain(*[doc_inverted_index.get(word, []) for word in words])
            )
            # candid_caption_line_idxes = set(chain(*[caption_inverted_index.get(word, []) for word in words]))

            # 获取候选行文本
            candid_doc_lines = [strip_doc_lines[idx] for idx in candid_doc_line_idxes]
            # candid_caption_lines = [strip_caption_lines[idx] for idx in candid_caption_line_idxes]

            # 计算匹配分数
            doc_scores = [
                get_char_match_score(strip_doc_line, strip_line)
                for strip_doc_line in candid_doc_lines
            ]
            # caption_scores = [get_char_match_score(strip_caption_line, strip_line) for strip_caption_line in candid_caption_lines]
            if "must be allocated to distinct" in line:
                debug(max(doc_scores))

            if len(strip_line) > 30:
                if doc_scores and max(doc_scores) > 0.5:
                    valid_lines.append(line)
            else:
                if doc_scores and max(doc_scores) > 0.8:
                    valid_lines.append(line)
        lines_of_pages.append(valid_lines)

    # out_path = "/home/ninziwei/projects/nougat_ocr/nougat/dataset/test/out"
    # with open(f"{out_path}/valid_lines.txt", "w", encoding="utf-8") as f:
    #     for lines in lines_of_pages:
    #         f.write("\n".join(lines))
    #         f.write("\n##### @@ #####\n")

    # 初始化指针和窗口大小
    min_window_size = 200
    start_pointer, end_pointer = 0, 0
    start_window_size, end_window_size = min_window_size, min_window_size
    page_start_positions = []  # 该页第一行文本在 doc_lines 中的索引
    page_end_positions = []  # 该页最后一行文本在 doc_lines 中的索引

    # 获得每一页的开始和结束行在 doc_lines 中的索引
    for page_lines in lines_of_pages:
        # 如果该页没有行，则认为没有有效位置
        if not page_lines:
            page_start_positions.append(-1)
            page_end_positions.append(-1)
            continue

        # 获得该页的开始和结束行
        start_line = squeeze_text(page_lines[0])
        end_line = squeeze_text(page_lines[-1])

        # 计算开始行的匹配分数
        start_window_end = min(start_pointer + start_window_size, len(strip_doc_lines))
        start_scores = [
            get_char_match_score(doc_line, start_line)
            for doc_line in strip_doc_lines[start_pointer:start_window_end]
        ]
        # start_idx: 下一页的开始行在 doc_lines 中的索引
        # end_idx: 当前页的结束行在 doc_lines 中的索引
        if start_scores and max(start_scores) > 0.8:
            start_idx = start_pointer + np.argmax(start_scores)
            page_start_positions.append(start_idx)
            start_pointer = start_idx + 1
        else:
            page_start_positions.append(-2)
            start_window_size += min_window_size

        # 计算结束行的匹配分数
        end_window_end = min(end_pointer + end_window_size, len(strip_doc_lines))
        end_scores = [
            get_char_match_score(doc_line, end_line)
            for doc_line in strip_doc_lines[end_pointer:end_window_end]
        ]

        debug(264, max(end_scores), end_pointer, end_window_end, end_line)
        if end_scores and max(end_scores) > 0.8:
            end_idx = end_pointer + np.argmax(end_scores)
            page_end_positions.append(end_idx)
            end_pointer = end_idx + 1
        else:
            page_end_positions.append(-2)
            end_window_size += min_window_size

        debug(231, page_start_positions[-1], start_line)
        debug(232, page_end_positions[-1], end_line)

    debug(272, page_start_positions)
    debug(273, page_end_positions)

    # 确定分割位置
    last_position = 0
    split_positions = []  # 该编号和下一个编号之间是分割位置
    bad_pages = []  # 如果开头结尾冲突，则认为这两页需要丢弃
    coinside_pages = []  # 两页重合的页码对

    for i, (end_idx, start_idx) in enumerate(
        zip(page_end_positions[:-1], page_start_positions[1:])
    ):
        debug(282, end_idx, start_idx)
        if end_idx == -1 and start_idx == -1:
            split_positions.append(last_position)
        elif end_idx == -2 and start_idx == -2:
            split_positions.append(last_position)
        elif end_idx < 0 and start_idx > 0:
            split_positions.append(start_idx - 1)
        elif start_idx < 0 and end_idx > 0:
            split_positions.append(end_idx)
        # 两者都大于0
        else:
            if start_idx >= end_idx:
                split_positions.append(end_idx)
                if start_idx == end_idx:
                    coinside_pages.append((i, i + 1))
            else:
                split_positions.append(last_position)
                bad_pages += [i, i + 1]
        last_position = split_positions[-1]

    # 根据分割位置拆分文档
    split_positions = [0] + split_positions + [len(doc_lines)]
    debug(298, split_positions)
    doc_text_by_pages = []
    for i in range(len(split_positions) - 1):
        doc_text_by_pages.append(
            "\n".join(doc_lines[split_positions[i] : split_positions[i + 1] + 1])
        )

    debug(304, len(doc_text_by_pages))
    return doc_text_by_pages, coinside_pages, bad_pages


def use_split_markdown():
    """
    主函数，处理命令行参数并执行拆分过程。

    流程：
    1. 解析命令行参数（Markdown文件、PDF文件、输出目录、图表信息等）
    2. 读取Markdown和PDF文件
    3. 调用split_markdown函数进行拆分
    4. 将拆分结果保存到指定目录
    5. 调用rasterize_paper函数将PDF页面转换为图像
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--md", type=str, help="Markdown file", required=False)
    parser.add_argument("--pdf", type=str, help="PDF File", required=False)
    parser.add_argument("--out", type=str, help="Out dir", required=False)
    parser.add_argument(
        "--figure",
        type=str,
        help="Figure info JSON",
    )
    parser.add_argument("--dpi", type=int, default=96)
    args = parser.parse_args()

    base_path = "/home/ninziwei/lyj/nougat/__test_new"
    fname = "2402.00041"
    args.md = f"{base_path}/markdown/{fname}.mmd"
    args.pdf = f"{base_path}/src/{fname}.pdf"
    args.figure = f"{base_path}/fig/{fname}.json"
    args.out = f"{base_path}/out"

    md = open(args.md, "r", encoding="utf-8").read().replace("\xa0", " ")
    pdf = pypdf.PdfReader(args.pdf)
    fig_info = json.load(open(args.figure, "r", encoding="utf-8"))

    pages, coinside_pages, bad_pages = split_markdown(md, pdf, fig_info)

    debug(341, len(pages))
    with open(f"{args.out}/{fname}.txt", "w", encoding="utf-8") as f:
        for page in pages:
            f.write(page)
            f.write("\n##### @@ #####\n")

    if args.out:
        # outpath = os.path.join(args.out, os.path.basename(args.pdf).partition(".")[0])
        outpath = os.path.join(args.out, os.path.basename(args.pdf))
        os.makedirs(outpath, exist_ok=True)
        found_pages = []
        for i, content in enumerate(pages):
            if content:
                with open(
                    os.path.join(outpath, "%02d.mmd" % (i + 1)),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(content)
                found_pages.append(i)
        rasterize_paper(args.pdf, outpath, dpi=args.dpi, pages=found_pages)


if __name__ == "__main__":
    # content = 'of the edge set of the original problem \(E\), i.e., \({|E|^{-1}\cdot\sum_{p=1}^{q}|E_{p}|}\)'
    # query = 'of the edge set of the original problem E, i.e., |E|−1 · Pq'
    # content = 'Givenitspracticalrelevance,numerousstudiesaboutthevehicleroutingproblem(VRP,DantzigandRamser1959)anditsvariantsexist(Vidaletal.2020).Typically,richVRPsoflarge-scalereal-worldapplicationsaresolvedbyheuristics.State-of-the-artmetaheuristicsusemostoftheircomputationtimesearchingforlocalimprovementsinanincumbentsolutionbymodifyingcustomersequenceswithinagiventourorchangingcustomer-vehicleassignments(Vidaletal.2013).Astheproblemsizeincreases,thenumberofpossiblelocalsearch(LS)operationsgrowsexponentially.Inresponse,complexityreductiontechniquesareappliedtolimitthesolutionspace.Decompositionandaggregationmethodsdividetheoriginalproblemintomultiplesmalleronesthataresolvedindependently(Santinietal.2023).PruninglimitstheLSoperators’explorationofnewsolutions(ArnoldandSörensen2019).Thesestrategiesmostlyfollowsimplerulestailoredtoaparticularproblem.Inpractice,however,solutionalgorithmsmustbescalableandadjustabletovariousproblemcharacteristics.Thus,weproposeageneralizablesolutionframeworkcalleddecompose-route-improve(DRI)thatreducesthecomplexityoflarge-scaleroutingproblemsusingdata-baseddecomposition.ThisapproachusesunsupervisedclusteringtosplitthecustomersofaVRPintoseparatesubsets.Itssimilaritymetriccombinescustomers’spatial,temporal,anddemandfeatureswiththeproblem’sobjectivefunctionandconstraints.Theresultingstand-alonesmall-sizedsub-VRPsaresolvedindependently.Thesolutiontotheoverallproblemisthecombinationoftheindividualsolutionsofthesubproblems.Finally,LS,prunedbasedoncustomers’spatial-temporal-demandsimilarity,resolvesunfavorableroutingdecisionsattheperimetersofthesubproblems.Thisapproachdemonstrateshighscalabilityandexpeditiouslyachieveshigh-qualitysolutionsforlarge-scaleVRPs.Thus,ourcontributiontothegrowingresearchfieldofheuristicdecompositionistwofold.'
    # query = 'contributiontothegrowingresearchfieldofheuristicdecompositionistwofold.'
    # print(decode_formula(content))
    # start_time = time.time()
    # print(get_char_match_score(content, query))
    # end_time = time.time()
    # print(f"Time taken: {end_time - start_time} seconds")
    # print(get_char_match_score(decode_formula(content), query))

    use_split_markdown()
