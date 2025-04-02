import os
import re
import argparse


def extract_name_from_single_tex(tex_file_path):
    """从 .tex 文件中提取 \\name{} 标签内容"""
    with open(tex_file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # 使用正则表达式提取name标签内容，支持嵌套大括号
    name_matches = re.findall(
        r"\\author\{((?:[^\{\}]+|\{(?:[^\{\}]+|\{[^\{\}]*\})*\})*)\}", content
    )

    # 去重处理
    unique_names = list(set(name_matches))

    return unique_names


def save_to_txt(output_folder_path, tex_file_path, names):
    """将提取到的 name 内容保存到 txt 文件"""
    # 确保输出文件夹存在
    os.makedirs(output_folder_path, exist_ok=True)

    # 构建输出txt文件路径
    txt_file_path = os.path.join(
        output_folder_path, tex_file_path.replace(".tex", ".txt")
    )
    print(output_folder_path)
    print(f"{tex_file_path}.txt")
    # 将name内容写入txt文件
    with open(txt_file_path, "a", encoding="utf-8") as file:
        for name in names:
            file.write(name + "\n")


def extract_names_from_tex(root_folder_path, output_folder_path):
    """遍历根目录下的文件夹，处理所有 .tex 文件"""
    # 遍历主文件夹中的所有子文件夹
    for root, _, files in os.walk(root_folder_path):
        for file in files:
            if file.endswith(".tex"):
                tex_file_path = os.path.join(root, file)
                print(tex_file_path)

                # 提取name标签内容
                names = extract_name_from_single_tex(tex_file_path)

                # 保存到指定输出路径的txt文件
                if names:
                    save_to_txt(output_folder_path, file, names)


def main():
    parser = argparse.ArgumentParser(
        description="Extract \name{} from .tex files and save them to .txt"
    )

    parser.add_argument(
        "root_folder_path",
        type=str,
        help="Root folder containing subfolders with .tex files",
    )
    parser.add_argument(
        "output_folder_path", type=str, help="Directory to save the output .txt files"
    )

    args = parser.parse_args()

    extract_names_from_tex(args.root_folder_path, args.output_folder_path)


if __name__ == "__main__":
    main()
