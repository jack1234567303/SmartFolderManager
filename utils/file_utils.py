import os
import subprocess
import time
import platform

# 常见拓展名到分类的映射
TYPE_MAPPING = {
    "文档": [".doc", ".docx", ".pdf", ".txt", ".md", ".rtf", ".odt", ".pages"],
    "表格": [".xls", ".xlsx", ".csv", ".tsv", ".ods", ".numbers"],
    "演示": [".ppt", ".pptx", ".key", ".odp"],
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".psd"],
    "视频": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
    "代码与脚本": [".py", ".java", ".c", ".cpp", ".cs", ".go", ".rs", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".sql", ".sh", ".bat", ".ps1"],
    "可执行与安装包": [".exe", ".msi", ".dmg", ".pkg", ".apk", ".deb", ".rpm"],
    "字体": [".ttf", ".otf", ".woff", ".woff2"]
}

def format_size(size_bytes: int) -> str:
    """格式化文件大小为易读字符串 (B, KB, MB, GB)"""
    if size_bytes < 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_idx = 0
    while size >= 1024.0 and unit_idx < len(units) - 1:
        size /= 1024.0
        unit_idx += 1
    if unit_idx == 0:
        return f"{int(size)} B"
    return f"{size:.2f} {units[unit_idx]}"

def format_time(timestamp: float) -> str:
    """格式化时间戳为易读时间字符串"""
    if not timestamp or timestamp <= 0:
        return "-"
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    except Exception:
        return "-"

def get_file_category_by_ext(ext: str) -> str:
    """根据文件拓展名获取分类名称"""
    ext_lower = ext.lower().strip()
    if not ext_lower:
        return "无拓展名"
    if not ext_lower.startswith("."):
        ext_lower = "." + ext_lower
    for category, exts in TYPE_MAPPING.items():
        if ext_lower in exts:
            return category
    return "其它"

def get_safe_destination_path(dst_path: str) -> str:
    """
    当目标路径已存在同名文件时，自动重命名添加后缀：file (1).txt，避免覆盖
    """
    if not os.path.exists(dst_path):
        return dst_path
    
    dir_name, base_name = os.path.split(dst_path)
    file_name, ext = os.path.splitext(base_name)
    
    counter = 1
    while True:
        new_name = f"{file_name} ({counter}){ext}"
        new_path = os.path.join(dir_name, new_name)
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def reveal_in_explorer(path: str):
    """在系统的文件资源管理器中打开并选中该文件/目录"""
    if not os.path.exists(path):
        return False
    path = os.path.abspath(path)
    current_os = platform.system()
    try:
        if current_os == "Windows":
            if os.path.isdir(path):
                subprocess.run(["explorer", path], check=False)
            else:
                subprocess.run(["explorer", "/select,", path], check=False)
            return True
        elif current_os == "Darwin":  # macOS
            subprocess.run(["open", "-R", path], check=False)
            return True
        else:  # Linux
            subprocess.run(["xdg-open", os.path.dirname(path) if os.path.isfile(path) else path], check=False)
            return True
    except Exception:
        return False

def open_file_with_default_app(path: str):
    """用系统默认程序打开文件"""
    if not os.path.exists(path):
        return False
    path = os.path.abspath(path)
    current_os = platform.system()
    try:
        if current_os == "Windows":
            os.startfile(path)
            return True
        elif current_os == "Darwin":
            subprocess.run(["open", path], check=False)
            return True
        else:
            subprocess.run(["xdg-open", path], check=False)
            return True
    except Exception:
        return False
