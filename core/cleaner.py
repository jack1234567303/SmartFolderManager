import os
from typing import List, Dict, Any, Tuple, Callable, Optional
from send2trash import send2trash
from utils.task_runner import CancellationToken

class Cleaner:
    """清理引擎：空文件夹扫描与清理"""

    @staticmethod
    def find_empty_folders(
        base_path: str,
        token: Optional[CancellationToken] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """从底向上扫描所有空文件夹"""
        if not os.path.exists(base_path) or not os.path.isdir(base_path):
            return []

        if log_cb:
            log_cb("正在扫描空目录...")

        empty_folders = []
        # 自底向上遍历，以便检测子目录被清空后的父目录
        for root, dirs, files in os.walk(base_path, topdown=False):
            if token and token.is_cancelled:
                break
            # 如果不是根目录本身，且目录下没有任何文件或子目录
            if root != base_path and not os.listdir(root):
                empty_folders.append({
                    "name": os.path.basename(root),
                    "path": root,
                    "rel_path": os.path.relpath(root, base_path)
                })

        if log_cb:
            log_cb(f"扫描完毕，共发现 {len(empty_folders)} 个空文件夹。")

        return empty_folders

    @staticmethod
    def clean_empty_folders(
        folder_paths: List[str],
        use_trash: bool = True,
        token: Optional[CancellationToken] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, int, List[str]]:
        """清理空文件夹"""
        total = len(folder_paths)
        success_count = 0
        fail_count = 0
        errors = []

        if total == 0:
            return 0, 0, []

        for idx, path in enumerate(folder_paths):
            if token and token.is_cancelled:
                break
            if not os.path.exists(path) or not os.path.isdir(path):
                continue
            
            # 双重保险：确保是真的空文件夹
            if os.listdir(path):
                fail_count += 1
                err = f"跳过非空文件夹: {path}"
                errors.append(err)
                if log_cb:
                    log_cb(err)
                continue

            try:
                if use_trash:
                    send2trash(path)
                else:
                    os.rmdir(path)
                success_count += 1
                if log_cb:
                    log_cb(f"✔ 已清理空文件夹: {os.path.basename(path)}")
            except Exception as e:
                fail_count += 1
                err = f"✖ 清理失败 [{path}]: {str(e)}"
                errors.append(err)
                if log_cb:
                    log_cb(err)

            if progress_cb:
                progress_cb((idx + 1) / total, f"清理中: {os.path.basename(path)}")

        return success_count, fail_count, errors
