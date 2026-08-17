import os
import shutil
import time
from typing import List, Dict, Tuple, Any, Callable, Optional
from utils.file_utils import (
    TYPE_MAPPING,
    get_file_category_by_ext,
    format_size,
    get_safe_destination_path
)
from utils.task_runner import CancellationToken
from core.undo_manager import undo_mgr
from ai.ai_service import AIService

SIZE_RANGES = {
    "小文件 (< 1MB)": (0, 1024 * 1024),
    "中等文件 (1MB ~ 10MB)": (1024 * 1024, 10 * 1024 * 1024),
    "大文件 (10MB ~ 100MB)": (10 * 1024 * 1024, 100 * 1024 * 1024),
    "超大文件 (> 100MB)": (100 * 1024 * 1024, float('inf'))
}

class Classifier:
    """智能文件分类引擎"""

    @staticmethod
    def get_candidate_files(src_folder: str) -> List[str]:
        """获取目标根目录下的所有可移动文件（不包含子目录内的文件）"""
        if not os.path.exists(src_folder) or not os.path.isdir(src_folder):
            return []
        files = []
        for item in os.listdir(src_folder):
            full_path = os.path.join(src_folder, item)
            if os.path.isfile(full_path):
                files.append(item)
        return files

    @staticmethod
    def calculate_category(file_path: str, mode: str, date_field: str = "mtime") -> str:
        """计算单个文件的目标分类名称"""
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename)

        if mode == "按文件类型":
            return get_file_category_by_ext(ext)

        elif mode == "按文件大小":
            size = os.path.getsize(file_path)
            for label, (min_s, max_s) in SIZE_RANGES.items():
                if min_s <= size < max_s:
                    return label
            return "未知大小"

        elif mode in ("按修改日期", "按创建日期"):
            stat = os.stat(file_path)
            t = stat.st_ctime if date_field == "ctime" else stat.st_mtime
            # 按 年-月 归档，避免生成太多单个日期的琐碎文件夹
            return time.strftime("%Y年%m月", time.localtime(t))

        elif mode == "AI 智能分类":
            return AIService.classify_file_by_ai(file_path)

        return "其它"

    @classmethod
    def preview_classification(
        cls,
        src_folder: str,
        mode: str,
        token: Optional[CancellationToken] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        预览分类计划（不实际移动文件）
        返回条目列表：[{"filename": ..., "current_path": ..., "target_category": ..., "size": ..., "status": ...}]
        """
        files = cls.get_candidate_files(src_folder)
        total = len(files)
        results = []

        if total == 0:
            if log_cb:
                log_cb("当前目录下未发现可分类的文件。")
            return []

        if log_cb:
            log_cb(f"开始生成分类预览，共发现 {total} 个文件...")

        for idx, fname in enumerate(files):
            if token and token.is_cancelled:
                if log_cb:
                    log_cb("用户取消了预览操作。")
                break

            full_path = os.path.join(src_folder, fname)
            size_str = format_size(os.path.getsize(full_path))
            
            try:
                cat = cls.calculate_category(full_path, mode)
                results.append({
                    "filename": fname,
                    "current_path": full_path,
                    "target_category": cat,
                    "target_dir": os.path.join(src_folder, cat),
                    "size": size_str,
                    "status": "待分类"
                })
            except Exception as e:
                results.append({
                    "filename": fname,
                    "current_path": full_path,
                    "target_category": "分类失败",
                    "target_dir": src_folder,
                    "size": size_str,
                    "status": f"错误: {str(e)}"
                })

            if progress_cb:
                progress_cb((idx + 1) / total, f"正在分析: {fname} ({(idx + 1)}/{total})")

        return results

    @classmethod
    def execute_classification(
        cls,
        src_folder: str,
        mode: str,
        token: Optional[CancellationToken] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, int, List[str]]:
        """
        执行文件分类移动操作
        返回 (成功数, 失败数, 错误信息列表)
        """
        files = cls.get_candidate_files(src_folder)
        total = len(files)
        success_count = 0
        fail_count = 0
        errors = []

        if total == 0:
            if log_cb:
                log_cb("当前目录下没有需要分类的文件。")
            return 0, 0, []

        tx = undo_mgr.create_transaction(f"{mode}分类", f"分类目录: {src_folder}")

        if log_cb:
            log_cb(f"开始执行【{mode}】，正在处理 {total} 个文件...")

        for idx, fname in enumerate(files):
            if token and token.is_cancelled:
                if log_cb:
                    log_cb("任务已被用户中止。")
                break

            src_path = os.path.join(src_folder, fname)
            try:
                cat = cls.calculate_category(src_path, mode)
                dst_dir = os.path.join(src_folder, cat)
                os.makedirs(dst_dir, exist_ok=True)

                raw_dst_path = os.path.join(dst_dir, fname)
                final_dst_path = get_safe_destination_path(raw_dst_path)

                shutil.move(src_path, final_dst_path)
                tx.add_action("move", src_path, final_dst_path)
                success_count += 1
                if log_cb:
                    log_cb(f"✔ 移动: {fname} -> {cat}/")
            except Exception as e:
                fail_count += 1
                err_msg = f"✖ 移动失败 [{fname}]: {str(e)}"
                errors.append(err_msg)
                if log_cb:
                    log_cb(err_msg)

            if progress_cb:
                progress_cb((idx + 1) / total, f"正在分类: {fname} ({(idx + 1)}/{total})")

        undo_mgr.commit_transaction(tx)

        if log_cb:
            log_cb(f"分类完成！成功: {success_count}, 失败: {fail_count}。操作已存入历史撤销栈。")

        return success_count, fail_count, errors
