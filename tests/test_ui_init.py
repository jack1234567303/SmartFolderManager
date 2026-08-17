import unittest
import os
import sys

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.app import App

class TestUIInitialization(unittest.TestCase):

    def test_app_creation(self):
        # 实例化 App 对象并验证核心组件属性正常挂载
        app = App()
        self.assertIsNotNone(app.file_tree)
        self.assertIsNotNone(app.tab_instances["classify"])
        self.assertIsNotNone(app.tab_instances["batch"])
        self.assertIsNotNone(app.tab_instances["search"])
        self.assertIsNotNone(app.tab_instances["tools"])
        self.assertIsNotNone(app.tab_instances["history"])
        
        # 销毁窗口，避免持续阻塞
        app.destroy()

if __name__ == '__main__':
    unittest.main()
