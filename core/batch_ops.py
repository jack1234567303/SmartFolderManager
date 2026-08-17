import os
from typing import List, Tuple, Dict, Any, Callable, Optional
from send2trash import send2trash
from utils.task_runner import CancellationToken
from core.undo_manager import undo_mgr

class BatchOps:
    """批量操作引擎：创建、重命名、安全删除"""

    @staticmethod
    def batch_create_folders(
        base_path: str,
        folder_names: List[str],
        prefix: str = "",
        suffix: str = "",
        token: Optional[CancellationToken] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, int, List[str]]:
        """批量创建文件夹"""
        if not os.path.exists(base_path):
            return 0, 0, ["目标路径不存在"]

        clean_names = [f"{prefix}{name.strip()}{suffix}" for name in folder_names if name.strip()]
        total = len(clean_names)
        success_count = 0
        fail_count = 0
        errors = []

        if total == 0:
            return 0, 0, ["没有有效的文件夹名称"]

        tx = undo_mgr.create_transaction("批量创建文件夹", f"根路径: {base_path}")

        for idx, name in enumerate(clean_names):
            if token and token.is_cancelled:
                break
            target_dir = os.path.join(base_path, name)
            try:
                os.makedirs(target_dir, exist_ok=True)
                tx.add_action("create", target_dir)
                success_count += 1
                if log_cb:
                    log_cb(f"✔ 创建成功: {name}")
            except Exception as e:
                fail_count += 1
                err = f"✖ 创建失败 [{name}]: {str(e)}"
                errors.append(err)
                if log_cb:
                    log_cb(err)

            if progress_cb:
                progress_cb((idx + 1) / total, f"正在创建: {name}")

        undo_mgr.commit_transaction(tx)
        return success_count, fail_count, errors

    @staticmethod
    def preview_batch_rename(
        base_path: str,
        name_pairs: List[Tuple[str, str]],
        prefix: str = "",
        suffix: str = ""
    ) -> List[Dict[str, Any]]:
        """
        预览批量重命名
        name_pairs: [ (old_name, new_name), ... ]
        """
        results = []
        for old, new in name_pairs:
            old = old.strip()
            new = new.strip()
            if not old:
                continue
            final_old = f"{prefix}{old}{suffix}"
            final_new = f"{prefix}{new}{suffix}"
            old_path = os.path.join(base_path, final_old)
            new_path = os.path.join(base_path, final_new)
            exists = os.path.exists(old_path)
            conflict = os.path.exists(new_path) and old_path != new_path
            
            status = "可重命名"
            if not exists:
                status = "原文件/夹不存在"
            elif conflict:
                status = "目标名称已存在"

            results.append({
                "old_name": final_old,
                "new_name": final_new,
                "old_path": old_path,
                "new_path": new_path,
                "status": status
            })
        return results

    @staticmethod
    def execute_batch_rename(
        base_path: str,
        name_pairs: List[Tuple[str, str]],
        prefix: str = "",
        suffix: str = "",
        token: Optional[CancellationToken] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, int, List[str]]:
        """执行批量重命名"""
        preview_list = BatchOps.preview_batch_rename(base_path, name_pairs, prefix, suffix)
        total = len(preview_list)
        success_count = 0
        fail_count = 0
        errors = []

        if total == 0:
            return 0, 0, ["未输入有效的重命名对应项"]

        tx = undo_mgr.create_transaction("批量重命名", f"路径: {base_path}")

        for idx, item in enumerate(preview_list):
            if token and token.is_cancelled:
                break
            if item["status"] != "可重命名":
                fail_count += 1
                err = f"✖ 跳过 [{item['old_name']}]: {item['status']}"
                errors.append(err)
                if log_cb:
                    log_cb(err)
                continue

            try:
                os.rename(item["old_path"], item["new_path"])
                tx.add_action("rename", item["old_path"], item["new_path"])
                success_count += 1
                if log_cb:
                    log_cb(f"✔ 重命名成功: {item['old_name']} -> {item['new_name']}")
            except Exception as e:
                fail_count += 1
                err = f"✖ 重命名失败 [{item['old_name']}]: {str(e)}"
                errors.append(err)
                if log_cb:
                    log_cb(err)

            if progress_cb:
                progress_cb((idx + 1) / total, f"正在重命名: {item['old_name']}")

        undo_mgr.commit_transaction(tx)
        return success_count, fail_count, errors

    @staticmethod
    def batch_safe_delete(
        base_path: str,
        target_names: List[str],
        prefix: str = "",
        suffix: str = "",
        token: Optional[CancellationToken] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, int, List[str]]:
        """
        批量安全删除（移至系统回收站，防误删）
        """
        clean_names = [f"{prefix}{name.strip()}{suffix}" for name in target_names if name.strip()]
        total = len(clean_names)
        success_count = 0
        fail_count = 0
        errors = []

        if total == 0:
            return 0, 0, ["没有指定要删除的文件或文件夹"]

        for idx, name in enumerate(clean_names):
            if token and token.is_cancelled:
                break
            target_path = os.path.join(base_path, name)
            if not os.path.exists(target_path):
                fail_count += 1
                err = f"✖ 目标不存在: {name}"
                errors.append(err)
                if log_cb:
                    log_cb(err)
                continue

            try:
                send2trash(target_path)
                success_count += 1
                if log_cb:
                    log_cb(f"🗑 已移至回收站: {name}")
            except Exception as e:
                fail_count += 1
                err = f"✖ 回收失败 [{name}]: {str(e)}"
                errors.append(err)
                if log_cb:
                    log_cb(err)

            if progress_cb:
                progress_cb((idx + 1) / total, f"正在移动到回收站: {name}")

        return success_count, fail_count, errors
