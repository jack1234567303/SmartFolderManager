import os
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch

from utils.config_manager import ConfigManager
from utils.file_utils import (
    get_file_category_by_ext,
    format_size,
    get_safe_destination_path,
    get_safe_child_path,
    validate_file_name,
)
from core.classifier import Classifier
from core.batch_ops import BatchOps
from core.search_engine import SearchEngine
from core.deduplicator import Deduplicator
from core.cleaner import Cleaner
from core.undo_manager import UndoManager
from ai.ai_service import AIService
from utils.task_runner import TaskRunner

class TestFolderManagerPro(unittest.TestCase):

    def setUp(self):
        # 创建一个临时测试目录
        self.test_dir = tempfile.mkdtemp(prefix="fp_test_")
        self.undo_manager = UndoManager(os.path.join(self.test_dir, "history.json"))
        
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
        s_count, f_count, errors = Classifier.execute_classification(
            self.test_dir,
            "按文件类型",
            undo_manager=self.undo_manager
        )
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
        history = self.undo_manager.get_history()
        self.assertTrue(len(history) > 0)
        latest_tx_id = history[0]["tx_id"]

        undo_res = self.undo_manager.undo_transaction(latest_tx_id)
        self.assertTrue(undo_res["success"])
        self.assertEqual(undo_res["restored"], 3)

        # 验证文件是否已完美复原回原目录
        self.assertTrue(os.path.exists(self.doc_file))
        self.assertTrue(os.path.exists(self.img_file))
        self.assertTrue(os.path.exists(self.code_file))

    def test_batch_operations(self):
        # 测试批量创建
        names = ["folder_a", "folder_b"]
        s_count, f_count, _ = BatchOps.batch_create_folders(
            self.test_dir,
            names,
            prefix="test_",
            undo_manager=self.undo_manager
        )
        self.assertEqual(s_count, 2)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test_folder_a")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test_folder_b")))

        # 测试批量重命名
        rename_pairs = [("test_folder_a", "renamed_a")]
        s_count, f_count, _ = BatchOps.execute_batch_rename(
            self.test_dir,
            rename_pairs,
            undo_manager=self.undo_manager
        )
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

    def test_file_name_and_path_validation(self):
        self.assertIsNone(validate_file_name("正常名称"))
        self.assertIsNotNone(validate_file_name("../outside"))
        self.assertIsNotNone(validate_file_name("CON.txt"))
        with self.assertRaises(ValueError):
            get_safe_child_path(self.test_dir, "../outside")

        success, failed, errors = BatchOps.batch_create_folders(
            self.test_dir,
            ["../outside", "nested/name"],
            undo_manager=self.undo_manager
        )
        self.assertEqual((success, failed), (0, 2))
        self.assertEqual(len(errors), 2)
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(self.test_dir), "outside")))

    def test_existing_folder_is_not_recorded_as_created(self):
        existing_dir = os.path.join(self.test_dir, "already_exists")
        os.makedirs(existing_dir)

        success, failed, errors = BatchOps.batch_create_folders(
            self.test_dir,
            ["already_exists"],
            undo_manager=self.undo_manager
        )

        self.assertEqual((success, failed), (0, 1))
        self.assertIn("已存在", errors[0])
        self.assertEqual(self.undo_manager.get_history(), [])

    def test_ai_category_cannot_escape_root(self):
        with patch.object(AIService, "classify_file_by_ai", return_value="../outside"):
            preview = Classifier.preview_classification(self.test_dir, "AI 智能分类")
            self.assertTrue(preview)
            self.assertTrue(all(item["status"].startswith("错误:") for item in preview))

            success, failed, _ = Classifier.execute_classification(
                self.test_dir,
                "AI 智能分类",
                undo_manager=self.undo_manager
            )
            self.assertEqual((success, failed), (0, 3))

    def test_undo_partial_failure_can_be_retried(self):
        source_one = os.path.join(self.test_dir, "source_one.txt")
        destination_one = os.path.join(self.test_dir, "destination_one.txt")
        with open(source_one, "w", encoding="utf-8") as f:
            f.write("one")
        os.rename(source_one, destination_one)

        source_two = os.path.join(self.test_dir, "source_two.txt")
        destination_two = os.path.join(self.test_dir, "destination_two.txt")
        tx = self.undo_manager.create_transaction("部分撤销测试")
        tx.add_action("move", source_one, destination_one)
        tx.add_action("move", source_two, destination_two)
        self.undo_manager.commit_transaction(tx)

        first_result = self.undo_manager.undo_transaction(tx.tx_id)
        self.assertFalse(first_result["success"])
        self.assertEqual(first_result["restored"], 1)
        self.assertTrue(os.path.exists(source_one))
        self.assertFalse(self.undo_manager.get_history()[0]["is_undone"])

        with open(destination_two, "w", encoding="utf-8") as f:
            f.write("two")
        second_result = self.undo_manager.undo_transaction(tx.tx_id)
        self.assertTrue(second_result["success"])
        self.assertEqual(second_result["restored"], 1)
        self.assertTrue(os.path.exists(source_two))
        self.assertTrue(self.undo_manager.get_history()[0]["is_undone"])

    def test_duplicate_snapshot_detects_stale_file(self):
        duplicate_path = os.path.join(self.test_dir, "duplicate.txt")
        with open(duplicate_path, "w", encoding="utf-8") as f:
            f.write("before")
        file_info = {
            "path": duplicate_path,
            "size_raw": os.path.getsize(duplicate_path),
        }
        expected_md5 = Deduplicator.get_file_md5(duplicate_path)

        with open(duplicate_path, "w", encoding="utf-8") as f:
            f.write("after")

        valid, reason = Deduplicator.verify_file_snapshot(file_info, expected_md5)
        self.assertFalse(valid)
        self.assertIn("变化", reason)

    def test_ai_semantic_search_checks_all_batches(self):
        items = [f"folder/item_{index}.txt" for index in range(81)]
        with patch.object(AIService, "_call_chat_completions", return_value="folder/item_80.txt") as call:
            matched = AIService.ai_semantic_search(items, "查找最后一个文件")

        self.assertEqual(matched, ["folder/item_80.txt"])
        self.assertEqual(call.call_count, 2)

    def test_api_key_can_come_from_environment(self):
        config_path = os.path.join(self.test_dir, "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write('{"ai": {"api_key": ""}}')

        with patch.dict(os.environ, {"SFM_AI_API_KEY": "from-env"}):
            config = ConfigManager(config_path)
            self.assertTrue(config.save_config())

        self.assertEqual(config.get("ai.api_key"), "from-env")
        with open(config_path, "r", encoding="utf-8") as f:
            saved_config = f.read()
        self.assertIn('"api_key": ""', saved_config)

    def test_task_runner_batches_high_frequency_logs(self):
        finished = threading.Event()
        log_messages = []

        def worker(token, progress_cb, log_cb):
            for index in range(100):
                log_cb(f"log-{index}")
            return True

        TaskRunner().run_task(
            worker,
            on_log=log_messages.append,
            on_success=lambda result: finished.set()
        )

        self.assertTrue(finished.wait(2))
        self.assertLess(len(log_messages), 100)
        self.assertIn("日志过于频繁", "\n".join(log_messages))

if __name__ == '__main__':
    unittest.main()
