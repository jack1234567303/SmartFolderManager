import json
import os
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "theme_mode": "System",  # "System", "Dark", "Light"
    "color_theme": "blue",   # "blue", "green", "dark-blue"
    "last_path": "",
    "ai": {
        "provider": "Moonshot",
        "base_url": "https://api.moonshot.cn/v1",
        "api_key": "",
        "model": "moonshot-v1-8k",
        "timeout": 25,
        "temperature": 0.2
    },
    "providers_preset": {
        "Moonshot": {
            "base_url": "https://api.moonshot.cn/v1",
            "model": "moonshot-v1-8k"
        },
        "DeepSeek": {
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat"
        },
        "OpenAI": {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini"
        },
        "Ollama (Local)": {
            "base_url": "http://localhost:11434/v1",
            "model": "qwen2.5:7b"
        },
        "Custom": {
            "base_url": "https://api.openai.com/v1",
            "model": "custom-model"
        }
    }
}

class ConfigManager:
    """全局配置管理器"""
    def __init__(self, config_path: str = "config.json"):
        # 获取相对于当前工作目录或脚本所在目录的绝对路径
        if not os.path.isabs(config_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_path = os.path.join(base_dir, config_path)
        else:
            self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                    # 递归合并默认配置以防缺少字段
                    return self._merge_dict(DEFAULT_CONFIG.copy(), user_cfg)
            except Exception as e:
                print(f"[ConfigManager] 加载配置失败: {e}，将使用默认配置")
        return DEFAULT_CONFIG.copy()

    def _merge_dict(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                base[k] = self._merge_dict(base[k], v)
            else:
                base[k] = v
        return base

    def save_config(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ConfigManager] 保存配置失败: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        支持通过点分路径获取配置项，如 get('ai.api_key')
        """
        keys = key_path.split(".")
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key_path: str, value: Any):
        """
        支持通过点分路径设置配置项，如 set('ai.api_key', 'sk-xxx')
        """
        keys = key_path.split(".")
        d = self.config
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value

# 全局单例
config_mgr = ConfigManager()
