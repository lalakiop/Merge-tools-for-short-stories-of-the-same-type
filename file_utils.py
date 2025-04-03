import os
import hashlib
import re
import shutil
import chardet


def compute_md5(file_path):
    """计算文件的 MD5 哈希值"""
    hasher = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
    except FileNotFoundError:
        return None
    return hasher.hexdigest()

def list_text_files(directory):
    """列出目录下的所有 .txt 文件"""
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".txt")]

def detect_updates(existing_novel, new_path):
    """检查外部小说文件是否比项目内的小说更新"""
    new_md5 = compute_md5(new_path)  # 计算外部新文件的MD5
    old_md5 = compute_md5(existing_novel["path"])  # 计算项目文件夹内小说的MD5

    return new_md5 != old_md5, new_md5  # 如果不同，说明有更新


def extract_chapters(file_path):
    """从小说文件中提取章节标题并排序"""
    
    chapter_pattern = re.compile(r"(^[\s\u3000]*第[\s\u3000]*(?:\d+|一|二|三|四|五|六|七|八|九|十)[\s\u3000]*章[\s\u3000]*(.*)?$|^第(\d+|[一二三四五六七八九十]+)章)")
    
    chapters = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.readlines()
            for i, line in enumerate(content):
                match = chapter_pattern.search(line)
                if match:
                    chapters.append({"title": line.strip(), "start_line": i})

        # 章节排序
        chapters.sort(key=lambda ch: int(re.findall(r"\d+", ch["title"])[0]) if re.findall(r"\d+", ch["title"]) else 0)

    except UnicodeDecodeError:
        with open(file_path, "r", encoding="gbk") as f:
            content = f.readlines()
            for i, line in enumerate(content):
                match = chapter_pattern.search(line)
                if match:
                    chapters.append({"title": line.strip(), "start_line": i})

        # 章节排序
        chapters.sort(key=lambda ch: int(re.findall(r"\d+", ch["title"])[0]) if re.findall(r"\d+", ch["title"]) else 0)
   # print(chapters)
    return chapters
    
    
def copy_file_to_path(source_file, target_folder):
    try:
        # 检查源文件是否存在
        if not os.path.isfile(source_file):
            print(f"源文件 {source_file} 不存在。")
            return None

        # 检查目标文件夹是否存在，如果不存在则创建
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        # 替换目标文件名中的空格
        target_filename = replace_spaces_in_filename(os.path.basename(source_file))
        target_file = os.path.join(target_folder, target_filename)

        # 复制文件
        shutil.copy2(source_file, target_file)
        #print(f"文件 {source_file} 已成功复制到 {target_file}。")
        convert_to_utf8(target_file)
        return target_file  # 返回修改后的路径

    except Exception as e:
        print(f"复制文件时出现错误: {e}")
        return None

def convert_to_utf8(file_path, output_path=None):
    """
    将非UTF-8编码的TXT文件转换为UTF-8编码。
    
    :param file_path: 原始TXT文件路径
    :param output_path: 转换后保存的路径，默认为原文件路径（覆盖原文件）
    :return: 转换后的文件路径
    """
    # 读取文件并检测编码
    with open(file_path, "rb") as f:
        raw_data = f.read()
        detected_encoding = chardet.detect(raw_data)['encoding']
    
    if not detected_encoding:
        raise ValueError(f"无法检测 {file_path} 的编码格式")
    
    # 读取文件内容并重新编码为UTF-8
    with open(file_path, "r", encoding=detected_encoding, errors="ignore") as f:
        content = f.read()
    
    # 如果没有指定输出路径，则覆盖原文件
    if output_path is None:
        output_path = file_path

    # 以UTF-8保存文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    #print(f"文件 {file_path} 已转换为 UTF-8 并保存至 {output_path}")
    
#替换文件名空格
def replace_spaces_in_filename(filename):
    """将文件名中的空格替换为 '-'"""
    return filename.replace(" ", "-")

    
def replace_space(file_path):
    """将文件路径中的文件名部分的空格替换为'--'并返回新路径"""
    dir_name = os.path.dirname(file_path)  # 获取文件所在目录
    file_name = os.path.basename(file_path)  # 获取文件名
    new_file_name = file_name.replace(" ", "--")  # 替换文件名中的空格
    new_file_path = os.path.join(dir_name, new_file_name)  # 重新拼接路径
    return new_file_path