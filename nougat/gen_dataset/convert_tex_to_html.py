import os
import subprocess
import argparse
import re
from pathlib import Path


def contains_documentclass(tex_file_path):
    """检查文件是否包含 \documentclass{} 或 \documentclass[]{} 标签"""
    pattern = re.compile(r"\\documentclass(\[[^\]]*\])?\{[^}]*\}")
    with open(tex_file_path, "r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            if pattern.search(line):
                return True
    return False


def remove_comments(tex_content):
    """删除 LaTeX 文本中的注释"""

    # 删除以 % 开头的注释行（允许空格/Tab），包括空行
    tex_content = re.sub(r"(?m)^\s*%.*(?:\n|$)", "", tex_content)

    # 删除行尾注释（非转义 %），包括可能没有 \n 的最后一行
    tex_content = re.sub(r"(?<!\\)%.*", "", tex_content)

    # 清理空行
    tex_content = re.sub(r"\n\s*\n", "\n", tex_content)

    return tex_content


def preprocess_tex(tex_file_path):
    """预处理 tex 文件"""
    with open(tex_file_path, "r", encoding="utf-8", errors="ignore") as file:
        content = file.read()

    # 删除注释
    content = remove_comments(content)

    author_pattern = re.compile(r"\\author\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}")
    title_pattern = re.compile(r"\\title\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}")

    # 如果文件中不包含 \maketitle，则删除 \author 和 \title 标签
    if not re.search(r"\\maketitle", content):
        content = re.sub(author_pattern, "", content)
        content = re.sub(title_pattern, "", content)

    with open(tex_file_path, "w", encoding="utf-8") as file:
        file.write(content.strip() + "\n")


def convert_tex_to_html(source_directory, target_directory, timeout=600):
    """
    将 LaTeX 文件转换为 HTML 格式，转换时间超过 timeout 会跳过
    :param timeout: 设置转换的最大时间（秒）
    """
    for root, _, files in os.walk(source_directory):
        subfolder_name = os.path.basename(root)
        for file in files:
            if file.endswith(".tex"):
                tex_file_path = os.path.join(root, file)
                if not contains_documentclass(tex_file_path):
                    continue
                preprocess_tex(tex_file_path)
                # 检查文件是否包含 \documentclass{} 标签
                xml_file_path = os.path.join(target_directory, subfolder_name + ".xml")
                html_file_path = os.path.join(
                    target_directory, subfolder_name + ".html"
                )

                # 使用 latexml 将 tex 文件转换为 xml 文件
                print(55, xml_file_path)
                command = (
                    f"latexml {tex_file_path} --dest={xml_file_path} --includestyles"
                )
                print(command)
                latex_command = command
                try:
                    # 使用 subprocess.run 并设置 timeout 参数
                    subprocess.run(
                        latex_command, check=True, shell=True, timeout=timeout
                    )
                    print(f"转换成功: {tex_file_path} -> {xml_file_path}")

                    # 使用 latexmlpost 将 xml 文件转换为 html 文件
                    post_command = (
                        f"latexmlpost {xml_file_path} --dest={html_file_path}"
                    )
                    subprocess.run(
                        post_command, check=True, shell=True, timeout=timeout
                    )
                    print(f"转换成功: {xml_file_path} -> {html_file_path}")
                    return True
                except subprocess.TimeoutExpired:
                    print(f"转换超时: {tex_file_path}，跳过该文件")
                    return False
                except subprocess.CalledProcessError as e:
                    print(f"转换失败: {tex_file_path}")
                    print(e)
                    return False


def main():
    parser = argparse.ArgumentParser(description="Convert LaTeX files to HTML")

    parser.add_argument(
        "source_directory", type=str, help="The source directory containing .tex files"
    )
    parser.add_argument(
        "--target_directory",
        type=str,
        help="The target directory to save converted HTML files",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout in seconds for each conversion (default is 600 seconds)",
    )

    args = parser.parse_args()

    target_directory = (
        args.target_directory
        if args.target_directory
        else Path(args.source_directory) / "html"
    )

    convert_tex_to_html(
        args.source_directory,
        target_directory,
        args.timeout,
    )


if __name__ == "__main__":
    main()
