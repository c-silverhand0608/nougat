import os
import subprocess
import argparse
from pathlib import Path


def debug(*args, **kwargs):
    # Uncomment the next line to enable debug logging
    # print(*args, **kwargs)
    pass


def convert_tex_to_html(tex_file_path, html_file_path, xml_file_path, timeout=300):
    """
    将 LaTeX 文件转换为 HTML 格式，转换时间超过 timeout 会跳过
    :param timeout: 设置转换的最大时间（秒）
    """
    # 使用 latexml 将 tex 文件转换为 xml 文件
    debug(55, xml_file_path)
    command = f"latexml {tex_file_path} --dest={xml_file_path} --includestyles"
    debug(command)
    latex_command = command
    try:
        # 使用 subprocess.run 并设置 timeout 参数
        subprocess.run(latex_command, check=True, shell=True, timeout=timeout)
        print(f"✅ 转换成功: {tex_file_path} -> {xml_file_path}")

        # 使用 latexmlpost 将 xml 文件转换为 html 文件
        post_command = f"latexmlpost {xml_file_path} --dest={html_file_path}"
        subprocess.run(post_command, check=True, shell=True, timeout=timeout)
        print(f"✅ 转换成功: {xml_file_path} -> {html_file_path}")
        return True
    except subprocess.TimeoutExpired:
        print(f"⚠️ 转换超时: {tex_file_path}，跳过该文件")
        return False
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 转换失败: {tex_file_path}")
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
        help="Timeout in seconds for each conversion (default is s00 seconds)",
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
