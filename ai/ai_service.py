import os
import re
import requests
from typing import List, Optional, Tuple, Dict, Any
from utils.config_manager import config_mgr
from utils.file_utils import validate_file_name
from ai.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    CLASSIFICATION_USER_PROMPT,
    SEMANTIC_SEARCH_SYSTEM_PROMPT,
    SEMANTIC_SEARCH_USER_PROMPT
)

class AIService:
    """通用大模型服务（兼容 OpenAI / DeepSeek / Moonshot / Ollama 协议）"""
    
    TEXT_EXTENSIONS = {
        '.txt', '.md', '.markdown', '.py', '.java', '.c', '.cpp', '.h', '.cs',
        '.js', '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
        '.csv', '.tsv', '.sql', '.sh', '.bat', '.log', '.ini', '.conf'
    }

    @classmethod
    def get_api_config(cls) -> Dict[str, Any]:
        return config_mgr.get("ai", {})

    @classmethod
    def test_connection(cls, base_url: str, api_key: str, model: str) -> Tuple[bool, str]:
        """测试模型连接连通性"""
        url = base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Ping: 请仅回复 'PONG'"}
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                return True, "连接成功！API 与模型响应正常。"
            else:
                return False, f"请求失败 (HTTP {resp.status_code}): {resp.text[:200]}"
        except requests.exceptions.Timeout:
            return False, "请求超时，请检查 Base URL 或网络连接。"
        except Exception as e:
            return False, f"连接异常: {str(e)}"

    @classmethod
    def _call_chat_completions(cls, system_prompt: str, user_prompt: str, max_tokens: int = 100) -> Optional[str]:
        cfg = cls.get_api_config()
        base_url = cfg.get("base_url", "https://api.moonshot.cn/v1").rstrip("/")
        api_key = cfg.get("api_key", "").strip()
        model = cfg.get("model", "moonshot-v1-8k")
        timeout = cfg.get("timeout", 20)
        temp = cfg.get("temperature", 0.2)

        if not api_key and "localhost" not in base_url and "127.0.0.1" not in base_url:
            raise ValueError("未配置 API Key，请在【设置】中配置大模型密钥后再试。")

        url = f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temp
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            raise RuntimeError(f"AI 接口返回错误 (HTTP {resp.status_code}): {resp.text[:150]}")

    @classmethod
    def extract_file_sample(cls, file_path: str, max_chars: int = 2000) -> str:
        """安全读取文件文本样本"""
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return ""
        
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in cls.TEXT_EXTENSIONS:
            # 对于非纯文本文件，返回简要元信息作为辅助上下文
            size_kb = os.path.getsize(file_path) / 1024
            return f"[二进制/多媒体文件，格式: {ext}，大小: {size_kb:.1f} KB]"

        # 尝试不同编码读取
        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read(max_chars)
                    return content.strip()
            except Exception:
                continue
        return ""

    @classmethod
    def classify_file_by_ai(cls, file_path: str) -> str:
        """通过 AI 分析文件内容并得出分类标签"""
        filename = os.path.basename(file_path)
        content_sample = cls.extract_file_sample(file_path)
        
        user_prompt = CLASSIFICATION_USER_PROMPT.format(
            filename=filename,
            content=content_sample if content_sample else "（无文本内容或为纯空文件）"
        )
        
        try:
            label = cls._call_chat_completions(CLASSIFICATION_SYSTEM_PROMPT, user_prompt, max_tokens=15)
            if not label:
                return "其它"
            # 过滤多余符号
            clean_label = label.replace("\n", "").replace("'", "").replace('"', "").strip()
            # 若返回过长则截断
            clean_label = clean_label[:12] if clean_label else "其它"
            if validate_file_name(clean_label):
                # AI 输出是不可信输入，不能直接成为目录名。
                print(f"[AIService] AI 返回了无效分类名称 [{filename}]，已回退到“其它”。")
                return "其它"
            return clean_label
        except Exception as e:
            print(f"[AIService] AI 分类失败 [{filename}]: {e}")
            raise e

    @classmethod
    def ai_semantic_search(
        cls,
        item_list: List[str],
        query: str,
        token: Optional[Any] = None,
        progress_cb: Optional[Any] = None,
        batch_size: int = 80
    ) -> List[str]:
        """通过 AI 进行自然语言语义文件查找"""
        if not item_list or not query.strip():
            return []

        if batch_size <= 0:
            raise ValueError("batch_size 必须大于 0")

        # 分批发送，避免只分析前一部分条目导致后面的文件永远搜不到。
        batches = [item_list[start:start + batch_size] for start in range(0, len(item_list), batch_size)]
        matched: List[str] = []
        try:
            for batch_index, batch in enumerate(batches, start=1):
                if token and token.is_cancelled:
                    break

                user_prompt = SEMANTIC_SEARCH_USER_PROMPT.format(
                    item_list="\n".join(batch),
                    query=query.strip()
                )
                response_text = cls._call_chat_completions(
                    SEMANTIC_SEARCH_SYSTEM_PROMPT,
                    user_prompt,
                    max_tokens=256
                )
                if response_text and "NO_MATCH" not in response_text:
                    batch_set = set(batch)
                    for raw_line in response_text.splitlines():
                        line = re.sub(r"^\s*(?:[-*•]\s*|\d+[.)]\s*)", "", raw_line).strip()
                        if line in batch_set and line not in matched:
                            matched.append(line)

                if progress_cb:
                    progress_cb(
                        0.3 + 0.6 * batch_index / len(batches),
                        f"正在分析第 {batch_index}/{len(batches)} 批条目..."
                    )
            return matched
        except Exception as e:
            print(f"[AIService] AI 语义搜索失败: {e}")
            raise e
