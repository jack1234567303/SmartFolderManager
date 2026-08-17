import os
import json
import time
import shutil
from typing import List, Dict, Any, Optional
from utils.file_utils import format_time

class FileAction:
    def __init__(self, action_type: str, src_path: str, dst_path: str = ""):
        self.action_type = action_type  # 'move', 'rename', 'create'
        self.src_path = src_path
        self.dst_path = dst_path
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "src_path": self.src_path,
            "dst_path": self.dst_path,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileAction":
        act = cls(data["action_type"], data["src_path"], data.get("dst_path", ""))
        act.timestamp = data.get("timestamp", time.time())
        return act


class Transaction:
    def __init__(self, tx_id: str, title: str, description: str = ""):
        self.tx_id = tx_id
        self.title = title
        self.description = description
        self.created_time = time.time()
        self.actions: List[FileAction] = []
        self.is_undone = False

    def add_action(self, action_type: str, src_path: str, dst_path: str = ""):
        self.actions.append(FileAction(action_type, src_path, dst_path))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "title": self.title,
            "description": self.description,
            "created_time": self.created_time,
            "is_undone": self.is_undone,
            "actions": [act.to_dict() for act in self.actions]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        tx = cls(data["tx_id"], data["title"], data.get("description", ""))
        tx.created_time = data.get("created_time", time.time())
        tx.is_undone = data.get("is_undone", False)
        tx.actions = [FileAction.from_dict(item) for item in data.get("actions", [])]
        return tx


class UndoManager:
    """操作历史与撤销管理器"""
    def __init__(self, history_file: str = "history.json", max_history: int = 50):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.history_file = os.path.join(base_dir, history_file)
        self.max_history = max_history
        self.transactions: List[Transaction] = self._load_history()

    def _load_history(self) -> List[Transaction]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    raw_list = json.load(f)
                    return [Transaction.from_dict(d) for d in raw_list]
            except Exception as e:
                print(f"[UndoManager] 加载历史记录失败: {e}")
        return []

    def _save_history(self):
        try:
            # 只保留最近 max_history 条记录
            self.transactions = self.transactions[-self.max_history:]
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([tx.to_dict() for tx in self.transactions], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[UndoManager] 保存历史记录失败: {e}")

    def create_transaction(self, title: str, description: str = "") -> Transaction:
        tx_id = f"tx_{int(time.time() * 1000)}"
        tx = Transaction(tx_id, title, description)
        return tx

    def commit_transaction(self, tx: Transaction):
        """提交事务并持久化"""
        if tx.actions:
            self.transactions.append(tx)
            self._save_history()

    def get_history(self) -> List[Dict[str, Any]]:
        """返回格式化的历史记录列表供 UI 展示"""
        records = []
        for tx in reversed(self.transactions):
            records.append({
                "tx_id": tx.tx_id,
                "title": tx.title,
                "description": tx.description,
                "time": format_time(tx.created_time),
                "count": len(tx.actions),
                "is_undone": tx.is_undone
            })
        return records

    def undo_transaction(self, tx_id: str) -> Dict[str, Any]:
        """
        执行指定事务的撤销操作（逆向恢复文件）
        """
        tx = next((t for t in self.transactions if t.tx_id == tx_id), None)
        if not tx:
            return {"success": False, "message": "未找到对应的历史记录", "restored": 0, "errors": []}
        
        if tx.is_undone:
            return {"success": False, "message": "该操作此前已经被撤销过了", "restored": 0, "errors": []}

        restored_count = 0
        errors = []

        # 逆序回滚所有动作
        for action in reversed(tx.actions):
            try:
                if action.action_type in ("move", "rename"):
                    current_path = action.dst_path
                    original_path = action.src_path
                    if not os.path.exists(current_path):
                        errors.append(f"文件不存在，无法恢复: {current_path}")
                        continue
                    # 确保原父级目录存在
                    os.makedirs(os.path.dirname(original_path), exist_ok=True)
                    shutil.move(current_path, original_path)
                    restored_count += 1
                elif action.action_type == "create":
                    created_dir = action.src_path
                    if os.path.exists(created_dir) and os.path.isdir(created_dir):
                        # 如果目录为空，则清理删除
                        if not os.listdir(created_dir):
                            os.rmdir(created_dir)
                            restored_count += 1
            except Exception as e:
                errors.append(f"回滚失败 [{action.src_path}]: {str(e)}")

        tx.is_undone = True
        self._save_history()

        return {
            "success": True,
            "message": f"成功撤销 {restored_count} 项操作",
            "restored": restored_count,
            "errors": errors
        }

    def clear_history(self):
        """清空历史记录"""
        self.transactions.clear()
        self._save_history()

# 全局单例
undo_mgr = UndoManager()
