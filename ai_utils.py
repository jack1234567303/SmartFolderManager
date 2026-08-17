import requests
import os
import time

MOONSHOT_API_URL = 'https://api.moonshot.cn/v1/chat/completions'
MOONSHOT_FILE_UPLOAD_URL = 'https://api.moonshot.cn/v1/files'
MOONSHOT_FILE_CONTENT_URL = 'https://api.moonshot.cn/v1/files/{file_id}/content'
API_KEY = 'sk-LJHkDQUZZkXaYtr1pC67YptfUrDrEZQLrM46CrN43mBmL44B'

def upload_file_to_moonshot(file_path):
    """上传文件到Moonshot，返回file_id"""
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f)}
        data = {'purpose': 'file-extract'}
        headers = {'Authorization': f'Bearer {API_KEY}'}
        resp = requests.post(MOONSHOT_FILE_UPLOAD_URL, headers=headers, files=files, data=data)
        if resp.ok:
            return resp.json().get('id')
    return None

def get_file_content_from_moonshot(file_id):
    """通过file_id获取文件内容"""
    headers = {'Authorization': f'Bearer {API_KEY}'}
    url = MOONSHOT_FILE_CONTENT_URL.format(file_id=file_id)
    resp = requests.get(url, headers=headers)
    if resp.ok:
        return resp.text
    return None

def classify_file_by_content(file_path):
    max_size = 2 * 1024 * 1024  # 2MB
    ext = os.path.splitext(file_path)[1].lower()
    text_exts = ['.txt', '.md', '.py', '.json', '.csv', '.log']
    # 优先本地读取小文本文件
    if ext in text_exts and os.path.getsize(file_path) <= max_size:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(4096)
        except Exception:
            return "未知"
    else:
        # 上传到Moonshot并获取内容
        file_id = upload_file_to_moonshot(file_path)
        if not file_id:
            return "上传失败"
        # 等待Moonshot解析完成（可适当sleep或轮询文件状态）
        for _ in range(10):
            content = get_file_content_from_moonshot(file_id)
            if content and len(content) > 10:
                break
            time.sleep(2)
        else:
            return "内容获取失败"
        # 可选：删除Moonshot上的文件，节省配额
        try:
            requests.delete(f'https://api.moonshot.cn/v1/files/{file_id}', headers={'Authorization': f'Bearer {API_KEY}'})
        except Exception:
            pass
        # 只取前4KB内容
        content = content[:4096]

    prompt = f"请判断以下文本内容属于哪一类，根据文件里的内容进行类别的划分，只返回类别名称：\n\n{content}"
    for _ in range(3):
        try:
            resp = requests.post(
                MOONSHOT_API_URL,
                headers={
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    "model": "moonshot-v1-8k",
                    "messages": [
                        {"role": "system", "content": "你是一个文件内容分类助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 20,
                    "temperature": 0.2
                },
                timeout=20
            )
            if resp.ok:
                result = resp.json()
                label = result['choices'][0]['message']['content'].strip()
                return label
            else:
                time.sleep(1)
        except Exception:
            time.sleep(1)
    return "未知"

def ai_search_folders(base_path, description):
    all_items = []
    for root, dirs, files in os.walk(base_path):
        rel_root = os.path.relpath(root, base_path)
        all_items.extend([os.path.join(rel_root, d) for d in dirs])
        all_items.extend([os.path.join(rel_root, f) for f in files])
    existing_items = "\n".join(all_items[:50])  # 限制最多50项，避免过长
    # Moonshot智能搜索：用自然语言描述，返回相关文件夹名
    prompt = (
        f"你需要从以下存在的文件和文件夹中，找到与用户描述最相关的条目：\n"
        f"存在的文件/文件夹列表：\n{existing_items}\n\n"
        f"用户搜索描述：{description}\n"
        f"请严格按照以下规则返回：\n"
        f"1. 只返回列表中实际存在的条目，不要虚构\n"
        f"2. 按相关性排序，每个条目占一行\n"
        f"3. 若没有匹配项，返回空"
    )
    for _ in range(3):
        try:
            resp = requests.post(
                MOONSHOT_API_URL,
                headers={
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    "model": "moonshot-v1-8k",
                    "messages": [
                        {"role": "system", "content": "你是一个文件智能搜索助手，请根据用户的内容描述，寻找对应的文件"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 128,
                    "temperature": 0.2
                },
                timeout=20
            )
            if resp.ok:
                result = resp.json()
                content = result['choices'][0]['message']['content']
                # 解析返回的文件夹名列表
                folders = [name.strip() for name in content.replace('\n', ',').split(',') if name.strip()]
                return folders
            else:
                time.sleep(1)
        except Exception:
            time.sleep(1)
    return []