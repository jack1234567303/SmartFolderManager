import os
import time
from ai_utils import ai_search_folders

def search_folders(base_path, name=None, min_size=None, max_size=None, mtime_range=None):
    """递归查找文件夹"""
    result = []
    for root, dirs, _ in os.walk(base_path):
        for d in dirs:
            try:
                path = os.path.join(root, d)
                stat = os.stat(path)
                if name and name not in d:
                    continue
                if min_size and stat.st_size < min_size:
                    continue
                if max_size and stat.st_size > max_size:
                    continue
                if mtime_range:
                    mtime = stat.st_mtime
                    if not (mtime_range[0] <= mtime <= mtime_range[1]):
                        continue
                result.append(path)
            except Exception:
                continue
    return result

def search_files(base_path, name=None, min_size=None, max_size=None, mtime_range=None):
    """递归查找文件"""
    result = []
    for root, _, files in os.walk(base_path):
        for f in files:
            try:
                path = os.path.join(root, f)
                stat = os.stat(path)
                if name and name not in f:
                    continue
                if min_size and stat.st_size < min_size:
                    continue
                if max_size and stat.st_size > max_size:
                    continue
                if mtime_range:
                    mtime = stat.st_mtime
                    if not (mtime_range[0] <= mtime <= mtime_range[1]):
                        continue
                result.append(path)
            except Exception:
                continue
    return result

def ai_search(base_path, description):
    try:
        return ai_search_folders(base_path, description)
    except Exception:
        return []
