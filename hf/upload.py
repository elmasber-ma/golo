"""upload.py - sube archivo/dir a Hugging Face Hub. Espejo estilo mimapp.

upload(token, local, repo_id, path_in_repo=".", repo_type="model", private=False)
El token NUNCA se guarda: solo argumento/env en ejecucion.
"""
from __future__ import annotations
import os


def upload(token: str, local: str, repo_id: str, path_in_repo: str = ".",
           repo_type: str = "model", private: bool = False,
           commit_message: str = "embeding chek") -> str:
    token = (token or os.getenv("HF_TOKEN") or "").strip()
    if not token:
        raise ValueError("falta token HF")
    if not os.path.exists(local):
        raise FileNotFoundError(f"no existe: {local}")
    from huggingface_hub import HfApi, create_repo
    api = HfApi(token=token)
    me = api.whoami().get("name", "?")
    create_repo(repo_id, token=token, repo_type=repo_type,
                private=private, exist_ok=True)
    if os.path.isfile(local):
        name = os.path.basename(local)
        dest = name if path_in_repo in (".", "") else path_in_repo.rstrip("/") + "/" + name \
            if not path_in_repo.endswith(name) else path_in_repo
        api.upload_file(path_or_fileobj=local, path_in_repo=dest,
                        repo_id=repo_id, repo_type=repo_type,
                        commit_message=commit_message)
        return f"OK archivo -> {repo_id}:{dest} (como {me})"
    api.upload_folder(folder_path=local, repo_id=repo_id, repo_type=repo_type,
                      path_in_repo=path_in_repo, commit_message=commit_message)
    return f"OK carpeta -> {repo_id}:{path_in_repo} (como {me})"
