import threading
import time
from typing import Callable, Any, Optional

class CancellationToken:
    """任务取消令牌"""
    def __init__(self):
        self._is_cancelled = False
        self._lock = threading.Lock()

    def cancel(self):
        with self._lock:
            self._is_cancelled = True

    @property
    def is_cancelled(self) -> bool:
        with self._lock:
            return self._is_cancelled

    def reset(self):
        with self._lock:
            self._is_cancelled = False


class TaskRunner:
    """
    异步任务执行器（具备 UI 节流防假死保护与线程安全调度）：
    将耗时的 I/O 操作、AI 网络请求、哈希扫描放到子线程中执行，
    并通过节流（Throttle）防止每秒数千次 UI 回调轰炸导致 Tkinter 事件循环卡死。
    """
    def __init__(self, root_widget: Any = None):
        self.root = root_widget
        self.current_token: Optional[CancellationToken] = None
        self.current_thread: Optional[threading.Thread] = None

    def set_root(self, root_widget: Any):
        self.root = root_widget

    def run_task(
        self,
        worker_func: Callable[[CancellationToken, Callable[[float, str], None], Callable[[str], None]], Any],
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_cancelled: Optional[Callable[[], None]] = None
    ) -> CancellationToken:
        """
        启动一个后台任务。
        worker_func 接收 3 个参数：(token, progress_callback, log_callback)
        """
        token = CancellationToken()
        self.current_token = token

        last_progress_time = 0.0
        progress_throttle_sec = 0.04  # 节流间隔约 40ms (25fps)，彻底杜绝大目录高频回调卡死事件循环

        def safe_ui_call(callback: Optional[Callable], *args):
            if not callback:
                return
            if self.root:
                try:
                    self.root.after(0, callback, *args)
                except Exception:
                    pass
            else:
                callback(*args)

        def thread_target():
            nonlocal last_progress_time

            def progress_bridge(percent: float, message: str = ""):
                nonlocal last_progress_time
                now = time.time()
                # 只有当进度是 0%、100% 或距离上次更新超过 40ms 时才派发 UI 更新
                if percent <= 0.001 or percent >= 0.999 or (now - last_progress_time) >= progress_throttle_sec:
                    last_progress_time = now
                    safe_ui_call(on_progress, percent, message)

            def log_bridge(msg: str):
                safe_ui_call(on_log, msg)

            try:
                result = worker_func(token, progress_bridge, log_bridge)
                if token.is_cancelled:
                    safe_ui_call(on_cancelled)
                else:
                    safe_ui_call(on_success, result)
            except Exception as e:
                if token.is_cancelled:
                    safe_ui_call(on_cancelled)
                else:
                    safe_ui_call(on_error, e)

        thread = threading.Thread(target=thread_target, daemon=True)
        self.current_thread = thread
        thread.start()
        return token

    def cancel_current_task(self):
        """取消当前正在运行的任务"""
        if self.current_token:
            self.current_token.cancel()
