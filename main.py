"""
智能文件夹管理大师 Pro (Smart Folder Manager Pro)
入口文件
"""
import sys
import os
import warnings

# 1. 修复 Windows 下 pythonw.exe 中 sys.stdout / sys.stderr 为 None 时
# 第三方库 (如 requests/urllib3) 抛出 Warning 导致静默崩溃的问题
if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    except Exception:
        pass

if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
    except Exception:
        pass

# 屏蔽非致命第三方依赖版本提示警告
warnings.filterwarnings("ignore")

# 2. 将项目根目录加入模块搜索路径
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

import traceback
from tkinter import messagebox

def main():
    try:
        from ui.app import App
        app = App()
        app.mainloop()
    except Exception as e:
        err_msg = traceback.format_exc()
        try:
            log_path = os.path.join(base_dir, "error.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        try:
            messagebox.showerror("启动异常", f"程序启动失败：\n{str(e)}\n\n详细日志已保存至 error.log")
        except Exception:
            pass

if __name__ == '__main__':
    main()
