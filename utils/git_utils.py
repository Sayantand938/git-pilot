# utils/git_utils.py
from git import Repo
import os

def get_repo(path="."):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path '{path}' does not exist")
    return Repo(path)

def get_staged_diff(repo):
    return repo.git.diff("--cached")

def commit(repo, message):
    if not message.strip():
        raise ValueError("Commit message is empty")
    repo.git.commit("-m", message)
