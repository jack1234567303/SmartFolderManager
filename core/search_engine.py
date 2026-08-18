import os
import re
from typing import List, Dict, Any, Callable, Optional
from utils.file_utils import format_size, format_time
from utils.task_runner import CancellationToken
from ai.ai_service import AIService

class SearchEngine:
    """多维度文件与目录搜索引擎"""

    @classmethod
    def search_local(
        cls,
        base_path: str,
        keyword: str = "",
        target_type: str = "全部",  # "全部", "仅文件", "仅文件夹"
        min_size_bytes: Optional[int] = None,
        max_size_bytes: Optional[int] = None,
        ext_filter: Optional[List[str]] = None,
        token: Optional[CancellationToken] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        递归多条件搜索
        """
        if not os.path.exists(base_path):
            return []

        results = []
        clean_kw = keyword.strip().lower()
        clean_exts = [e.lower() if e.startswith('.') else f".{e.lower()}" for e in ext_filter] if ext_filter else []

        scanned_count = 0

        for root, dirs, files in os.walk(base_path):
            if token and token.is_cancelled:
                break

            # 文件夹匹配
            if target_type in ("全部", "仅文件夹"):
                for d in dirs:
                    scanned_count += 1
                    full_path = os.path.join(root, d)
                    if clean_kw and clean_kw not in d.lower():
                        continue
                    try:
                        stat = os.stat(full_path)
                        results.append({
                            "name": d,
                            "path": full_path,
                            "rel_path": os.path.relpath(full_path, base_path),
                            "type": "文件夹",
                            "size_raw": 0,
                            "size": "-",
                            "mtime": format_time(stat.st_mtime),
                            "mtime_raw": stat.st_mtime
                        })
                    except Exception:
                        continue

            # 文件匹配
            if target_type in ("全部", "仅文件"):
                for f in files:
                    scanned_count += 1
                    full_path = os.path.join(root, f)
                    if clean_kw and clean_kw not in f.lower():
                        continue
                    
                    _, ext = os.path.splitext(f)
                    if clean_exts and ext.lower() not in clean_exts:
                        continue

                    try:
                        stat = os.stat(full_path)
                        f_size = stat.st_size
                        if min_size_bytes is not None and f_size < min_size_bytes:
                            continue
                        if max_size_bytes is not None and f_size > max_size_bytes:
                            continue

                        results.append({
                            "name": f,
                            "path": full_path,
                            "rel_path": os.path.relpath(full_path, base_path),
                            "type": ext.lower() if ext else "文件",
                            "size_raw": f_size,
                            "size": format_size(f_size),
                            "mtime": format_time(stat.st_mtime),
                            "mtime_raw": stat.st_mtime
                        })
                    except Exception:
                        continue

            if progress_cb and scanned_count % 100 == 0:
                progress_cb(0.5, f"已扫描 {scanned_count} 个条目，匹配 {len(results)} 项...")

        if log_cb:
            log_cb(f"搜索完毕，扫描了 {scanned_count} 个条目，共找到 {len(results)} 个匹配结果。")

        return results

    @classmethod
    def search_ai_semantic(
        cls,
        base_path: str,
        query: str,
        token: Optional[CancellationToken] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        AI 自然语言语义搜索
        """
        if not os.path.exists(base_path):
            return []

        if log_cb:
            log_cb("正在遍历目录并提取条目列表...")

        all_rel_paths = []
        path_map = {}

        for root, dirs, files in os.walk(base_path):
            if token and token.is_cancelled:
                break
            for item in dirs + files:
                full = os.path.join(root, item)
                rel = os.path.relpath(full, base_path)
                all_rel_paths.append(rel)
                path_map[rel] = full

        if not all_rel_paths:
            return []

        if log_cb:
            log_cb(f"共发现 {len(all_rel_paths)} 个条目，将分批交给 AI 分析，避免遗漏后面的文件。")

        if progress_cb:
            progress_cb(0.3, "正在请求大模型进行语义意图匹配...")

        matched_rel_paths = AIService.ai_semantic_search(
            all_rel_paths,
            query,
            token=token,
            progress_cb=progress_cb
        )

        results = []
        for rel in matched_rel_paths:
            if rel in path_map:
                full_path = path_map[rel]
                is_dir = os.path.isdir(full_path)
                try:
                    stat = os.stat(full_path)
                    results.append({
                        "name": os.path.basename(full_path),
                        "path": full_path,
                        "rel_path": rel,
                        "type": "文件夹" if is_dir else (os.path.splitext(full_path)[1] or "文件"),
                        "size_raw": stat.st_size if not is_dir else 0,
                        "size": format_size(stat.st_size) if not is_dir else "-",
                        "mtime": format_time(stat.st_mtime),
                        "mtime_raw": stat.st_mtime
                    })
                except Exception:
                    continue

        if log_cb:
            log_cb(f"AI 语义搜索完成，返回了 {len(results)} 个高相关度结果。")

        return results
