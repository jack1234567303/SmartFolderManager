import os
import shutil
import time
from ai_utils import classify_file_by_content

def classify_by_type(src_folder):
    # 按文件类型分类
    type_map = {
        '文档': ['.doc', '.docx', '.pdf', '.txt', '.xls', '.xlsx', '.ppt', '.pptx'],
        '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
        '视频': ['.mp4', '.avi', '.mov', '.wmv'],
        # ...可扩展
    }
    for root, _, files in os.walk(src_folder):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            src_path = os.path.join(root, f)
            # 跳过已归档文件夹
            if os.path.dirname(src_path) != src_folder:
                continue
            for k, v in type_map.items():
                if ext in v:
                    dst_dir = os.path.join(src_folder, k)
                    os.makedirs(dst_dir, exist_ok=True)
                    try:
                        shutil.move(src_path, os.path.join(dst_dir, f))
                    except Exception as e:
                        print(f"移动文件失败: {src_path} -> {dst_dir}, 错误: {e}")
                    break

def classify_by_size(src_folder, size_ranges):
    # 按文件大小分类
    for root, _, files in os.walk(src_folder):
        for f in files:
            src_path = os.path.join(root, f)
            if os.path.dirname(src_path) != src_folder:
                continue
            size = os.path.getsize(src_path)
            for label, (min_s, max_s) in size_ranges.items():
                if min_s <= size < max_s:
                    dst_dir = os.path.join(src_folder, label)
                    os.makedirs(dst_dir, exist_ok=True)
                    try:
                        shutil.move(src_path, os.path.join(dst_dir, f))
                    except Exception as e:
                        print(f"移动文件失败: {src_path} -> {dst_dir}, 错误: {e}")
                    break

def classify_by_date(src_folder, mode='created'):
    # 按创建/修改日期分类
    for root, _, files in os.walk(src_folder):
        for f in files:
            src_path = os.path.join(root, f)
            if os.path.dirname(src_path) != src_folder:
                continue
            if mode == 'created':
                t = os.path.getctime(src_path)
            else:
                t = os.path.getmtime(src_path)
            date_str = time.strftime('%Y-%m-%d', time.localtime(t))
            dst_dir = os.path.join(src_folder, date_str)
            os.makedirs(dst_dir, exist_ok=True)
            try:
                shutil.move(src_path, os.path.join(dst_dir, f))
            except Exception as e:
                print(f"移动文件失败: {src_path} -> {dst_dir}, 错误: {e}")

def classify_by_ai(src_folder):
    # AI内容分类
    for root, _, files in os.walk(src_folder):
        for f in files:
            src_path = os.path.join(root, f)
            if os.path.dirname(src_path) != src_folder:
                continue
            try:
                label = classify_file_by_content(src_path)
                dst_dir = os.path.join(src_folder, label)
                os.makedirs(dst_dir, exist_ok=True)
                shutil.move(src_path, os.path.join(dst_dir, f))
            except Exception as e:
                print(f"AI分类移动失败: {src_path}, 错误: {e}")

def preview_classify_by_type(src_folder):
    """返回每个文件将被归入的类型，不移动文件"""
    type_map = {
        '文档': ['.doc', '.docx', '.pdf', '.txt', '.xls', '.xlsx', '.ppt', '.pptx'],
        '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
        '视频': ['.mp4', '.avi', '.mov', '.wmv'],
    }
    result = []
    files = [f for f in os.listdir(src_folder) if os.path.isfile(os.path.join(src_folder, f))]
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        found = False
        for k, v in type_map.items():
            if ext in v:
                result.append((f, k))
                found = True
                break
        if not found:
            result.append((f, '其它'))
    return result

def preview_classify_by_size(src_folder, size_ranges):
    """返回每个文件将被归入的大小分类，不移动文件"""
    result = []
    files = [f for f in os.listdir(src_folder) if os.path.isfile(os.path.join(src_folder, f))]
    for f in files:
        size = os.path.getsize(os.path.join(src_folder, f))
        found = False
        for label, (min_s, max_s) in size_ranges.items():
            if min_s <= size < max_s:
                result.append((f, label))
                found = True
                break
        if not found:
            result.append((f, '未知'))
    return result

def preview_classify_by_date(src_folder, mode='created'):
    """返回每个文件将被归入的日期分类，不移动文件"""
    result = []
    files = [f for f in os.listdir(src_folder) if os.path.isfile(os.path.join(src_folder, f))]
    for f in files:
        path = os.path.join(src_folder, f)
        if mode == 'created':
            t = os.path.getctime(path)
        else:
            t = os.path.getmtime(path)
        date_str = time.strftime('%Y-%m-%d', time.localtime(t))
        result.append((f, date_str))
    return result

def preview_classify_by_ai(src_folder):
    """返回每个文件的AI分类，不移动文件"""
    result = []
    files = [f for f in os.listdir(src_folder) if os.path.isfile(os.path.join(src_folder, f))]
    for f in files:
        path = os.path.join(src_folder, f)
        label = classify_file_by_content(path)
        result.append((f, label))
    return result
