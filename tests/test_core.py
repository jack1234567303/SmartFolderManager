import os
import shutil
import tempfile
import unittest

from utils.config_manager import config_mgr
from utils.file_utils import get_file_category_by_ext, format_size, get_safe_destination_path
from core.classifier import Classifier
from core.batch_ops import BatchOps
from core.search_engine import SearchEngine
from core.deduplicator import Deduplicator
from core.cleaner import Cleaner
from core.undo_manager import undo_mgr

class TestFolderManagerPro(unittest.TestCase):

    def setUp(self):
        # 创建一个临时测试目录
        self.test_dir = tempfile.mkdtemp(prefix="fp_test_")
        
        # 创建一些样本文件
        self.doc_file = os.path.join(self.test_dir, "report.docx")
        with open(self.doc_file, "w", encoding="utf-8") as f:
            f.write("This is a test doc report.")

        self.img_file = os.path.join(self.test_dir, "photo.png")
        with open(self.img_file, "w", encoding="utf-8") as f:
            f.write("Binary photo content simulation.")

        self.code_file = os.path.join(self.test_dir, "script.py")
        with open(self.code_file, "w", encoding="utf-8") as f:
            f.write("print('hello test')")

        # 创建一个空文件夹
        self.empty_dir = os.path.join(self.test_dir, "empty_subfolder")
        os.makedirs(self.empty_dir, exist_ok=True)

    def tearDown(self):
        # 清理临时测试目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_file_category(self):
        self.assertEqual(get_file_category_by_ext(".docx"), "文档")
        self.assertEqual(get_file_category_by_ext(".png"), "图片")
        self.assertEqual(get_file_category_by_ext(".py"), "代码与脚本")
        self.assertEqual(get_file_category_by_ext(".unknown"), "其它")

    def test_safe_destination_path(self):
        existing_path = self.doc_file
        safe_path = get_safe_destination_path(existing_path)
        self.assertTrue(safe_path.endswith("report (1).docx"))

    def test_classification_and_undo(self):
        # 1. 预览分类
        preview = Classifier.preview_classification(self.test_dir, "按文件类型")
        self.assertEqual(len(preview), 3)

        # 2. 执行分类
        s_count, f_count, errors = Classifier.execute_classification(self.test_dir, "按文件类型")
        self.assertEqual(s_count, 3)
        self.assertEqual(f_count, 0)

        # 验证文件是否被移动到对应子文件夹
        doc_dir = os.path.join(self.test_dir, "文档")
        img_dir = os.path.join(self.test_dir, "图片")
        code_dir = os.path.join(self.test_dir, "代码与脚本")

        self.assertTrue(os.path.exists(os.path.join(doc_dir, "report.docx")))
        self.assertTrue(os.path.exists(os.path.join(img_dir, "photo.png")))
        self.assertTrue(os.path.exists(os.path.join(code_dir, "script.py")))

        # 3. 测试一键撤销
        history = undo_mgr.get_history()
        self.assertTrue(len(history) > 0)
        latest_tx_id = history[0]["tx_id"]

        undo_res = undo_mgr.undo_transaction(latest_tx_id)
        self.assertTrue(undo_res["success"])
        self.assertEqual(undo_res["restored"], 3)

        # 验证文件是否已完美复原回原目录
        self.assertTrue(os.path.exists(self.doc_file))
        self.assertTrue(os.path.exists(self.img_file))
        self.assertTrue(os.path.exists(self.code_file))

    def test_batch_operations(self):
        # 测试批量创建
        names = ["folder_a", "folder_b"]
        s_count, f_count, _ = BatchOps.batch_create_folders(self.test_dir, names, prefix="test_")
        self.assertEqual(s_count, 2)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test_folder_a")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test_folder_b")))

        # 测试批量重命名
        rename_pairs = [("test_folder_a", "renamed_a")]
        s_count, f_count, _ = BatchOps.execute_batch_rename(self.test_dir, rename_pairs)
        self.assertEqual(s_count, 1)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "renamed_a")))

    def test_deduplicator(self):
        # 创建两份内容完全相同的重复文件
        dup1 = os.path.join(self.test_dir, "dup1.txt")
        dup2 = os.path.join(self.test_dir, "dup2.txt")
        content = "Exact duplicate content for MD5 verification."
        with open(dup1, "w", encoding="utf-8") as f:
            f.write(content)
        with open(dup2, "w", encoding="utf-8") as f:
            f.write(content)

        dup_groups = Deduplicator.find_duplicate_files(self.test_dir)
        self.assertEqual(len(dup_groups), 1)
        self.assertEqual(dup_groups[0]["count"], 2)

    def test_cleaner(self):
        empty_dirs = Cleaner.find_empty_folders(self.test_dir)
        self.assertEqual(len(empty_dirs), 1)
        self.assertEqual(empty_dirs[0]["name"], "empty_subfolder")

    def test_search_engine(self):
        results = SearchEngine.search_local(self.test_dir, keyword="report", target_type="仅文件")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "report.docx")

if __name__ == '__main__':
    unittest.main()
