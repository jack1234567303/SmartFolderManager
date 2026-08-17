import os
import shutil
import zipfile

def batch_create_folders(base_path, names):
    results = []
    for name in names:
        try:
            os.makedirs(os.path.join(base_path, name), exist_ok=True)
            results.append((name, True))
        except Exception as e:
            results.append((name, False, str(e)))
    return results

def batch_delete_folders(base_path, names):
    results = []
    for name in names:
        try:
            shutil.rmtree(os.path.join(base_path, name), ignore_errors=True)
            results.append((name, True))
        except Exception as e:
            results.append((name, False, str(e)))
    return results

def batch_rename_folders(base_path, old_new_names):
    results = []
    for old, new in old_new_names:
        try:
            os.rename(os.path.join(base_path, old), os.path.join(base_path, new))
            results.append((old, new, True))
        except Exception as e:
            results.append((old, new, False, str(e)))
    return results

def batch_chmod_folders(base_path, names, mode):
    for name in names:
        os.chmod(os.path.join(base_path, name), mode)
