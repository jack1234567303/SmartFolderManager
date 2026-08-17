import os
import hashlib
from typing import List, Dict, Any, Callable, Optional
from collections import defaultdict
from utils.file_utils import format_size, format_time
from utils.task_runner import CancellationToken

class Deduplicator:
    """高效重复文件查重引擎（大小预筛 + 块流式 MD5 校验）"""

    @staticmethod
    def get_file_md5(file_path: str, chunk_size: int = 65536, token: Optional[CancellationToken] = None) -> Optional[str]:
        """流式分块计算 MD5 哈希"""
        md5_obj = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    if token and token.is_cancelled:
                        return None
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    md5_obj.update(chunk)
            return md5_obj.hexdigest()
        except Exception:
            return None

    @classmethod
    def find_duplicate_files(
        cls,
        base_path: str,
        token: Optional[CancellationToken] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        扫描重复文件
        返回重复分组列表：[{"md5": ..., "size_str": ..., "wasted_bytes": ..., "files": [...]}]
        """
        if not os.path.exists(base_path):
            return []

        if log_cb:
            log_cb(f"【阶段 1/2】正在遍历目录，根据文件字节大小进行快速预分组...")

        size_map: Dict[int, List[str]] = defaultdict(list)
        total_files = 0

        for root, _, files in os.walk(base_path):
            if token and token.is_cancelled:
                return []
            for f in files:
                full_path = os.path.join(root, f)
                try:
                    f_size = os.path.getsize(full_path)
                    if f_size > 0:  # 忽略 0 字节文件
                        size_map[f_size].append(full_path)
                        total_files += 1
                except Exception:
                    continue

        # 过滤出大小相同且数量 >= 2 的候选文件
        candidates: List[Tuple[int, List[str]]] = [(size, paths) for size, paths in size_map.items() if len(paths) >= 2]
        candidate_count = sum(len(paths) for _, paths in candidates)

        if log_cb:
            log_cb(f"共扫描 {total_files} 个文件，发现 {len(candidates)} 组可能重复的大小候选（共 {candidate_count} 个文件）。")
            log_cb(f"【阶段 2/2】正在计算 MD5 校验哈希...")

        duplicate_groups = []
        processed_candidates = 0

        for size, paths in candidates:
            if token and token.is_cancelled:
                break

            md5_map = defaultdict(list)
            for path in paths:
                if token and token.is_cancelled:
                    break
                md5_val = cls.get_file_md5(path, token=token)
                processed_candidates += 1
                if md5_val:
                    md5_map[md5_val].append(path)

                if progress_cb:
                    progress_cb(
                        processed_candidates / max(1, candidate_count),
                        f"校验哈希: {os.path.basename(path)} ({processed_candidates}/{candidate_count})"
                    )

            # 找出真正 MD5 完全相同的文件
            for md5_val, dup_paths in md5_map.items():
                if len(dup_paths) >= 2:
                    file_details = []
                    for p in dup_paths:
                        try:
                            stat = os.stat(p)
                            file_details.append({
                                "name": os.path.basename(p),
                                "path": p,
                                "rel_path": os.path.relpath(p, base_path),
                                "size": format_size(stat.st_size),
                                "size_raw": stat.st_size,
                                "mtime": format_time(stat.st_mtime)
                            })
                        except Exception:
                            continue

                    wasted_bytes = (len(dup_paths) - 1) * size
                    duplicate_groups.append({
                        "md5": md5_val,
                        "size_str": format_size(size),
                        "count": len(dup_paths),
                        "wasted_bytes": wasted_bytes,
                        "wasted_str": format_size(wasted_bytes),
                        "files": file_details
                    })

        total_wasted = sum(g["wasted_bytes"] for g in duplicate_groups)
        if log_cb:
            log_cb(f"查重完成！共发现 {len(duplicate_groups)} 组重复文件，可释放空间: {format_size(total_wasted)}。")

        return duplicate_groups
