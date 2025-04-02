import os
import subprocess
import argparse
import re


def contains_documentclass(tex_file_path):
    """检查文件是否包含 \documentclass{} 或 \documentclass[]{} 标签"""
    pattern = re.compile(r'\\documentclass(\[[^\]]*\])?\{[^}]*\}')
    with open(tex_file_path, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            if pattern.search(line):
                return True
    return False


def convert_tex_to_html(source_directory, target_directory, timeout=600):
    """
    将 LaTeX 文件转换为 HTML 格式，转换时间超过 timeout 会跳过
    :param timeout: 设置转换的最大时间（秒）
    """
    for root, _, files in os.walk(source_directory):
        subfolder_name = os.path.basename(root)
        for file in files:
            if file.endswith('.tex'):
                tex_file_path = os.path.join(root, file)

                # 检查文件是否包含 \documentclass{} 标签
                if contains_documentclass(tex_file_path):
                    xml_file_path = os.path.join(target_directory, subfolder_name + '.xml')
                    html_file_path = os.path.join(target_directory, subfolder_name + '.html')

                    # 使用 latexml 将 tex 文件转换为 xml 文件
                    latex_command = f"latexml {tex_file_path} --dest={xml_file_path} --includestyles"
                    try:
                        # 使用 subprocess.run 并设置 timeout 参数
                        subprocess.run(latex_command, check=True, shell=True, timeout=timeout)
                        print(f"转换成功: {tex_file_path} -> {xml_file_path}")

                        # 使用 latexmlpost 将 xml 文件转换为 html 文件
                        post_command = f"latexmlpost {xml_file_path} --dest={html_file_path}"
                        subprocess.run(post_command, check=True, shell=True, timeout=timeout)
                        print(f"转换成功: {xml_file_path} -> {html_file_path}")
                    except subprocess.TimeoutExpired:
                        print(f"转换超时: {tex_file_path}，跳过该文件")
                        continue
                    except subprocess.CalledProcessError as e:
                        print(f"转换失败: {tex_file_path}")
                        print(e)
                        continue


def main():
    # 创建命令行解析器
    parser = argparse.ArgumentParser(description="Convert LaTeX files to HTML")

    # 定义命令行参数
    parser.add_argument('source_directory', type=str, help="The source directory containing .tex files")
    parser.add_argument('target_directory', type=str, help="The target directory to save converted HTML files")
    parser.add_argument('--timeout', type=int, default=600,
                        help="Timeout in seconds for each conversion (default is 600 seconds)")

    # 解析命令行参数
    args = parser.parse_args()

    # 调用转换函数
    convert_tex_to_html(args.source_directory, args.target_directory, args.timeout)


if __name__ == "__main__":
    main()
