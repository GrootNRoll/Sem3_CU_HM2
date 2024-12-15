import os
import subprocess
import argparse
from datetime import datetime
from collections import defaultdict


def get_git_commits(repo_path, since_date):
    """
    Возвращает список коммитов с их данными (хэш, дата, файлы и папки) после указанной даты.
    """
    git_log_cmd = [
        "git", "log", f"--since={since_date}", "--name-only", "--pretty=format:%H|%cd", "--date=iso"
    ]

    try:
        result = subprocess.run(git_log_cmd, cwd=repo_path, stdout=subprocess.PIPE, text=True, check=True)
        log_data = result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ошибка при выполнении git log: {e}")

    commits = []
    current_commit = None
    for line in log_data.splitlines():
        if "|" in line:
            if current_commit:
                commits.append(current_commit)
            commit_hash, commit_date = line.split("|", 1)
            current_commit = {
                "hash": commit_hash,
                "date": commit_date.strip(),
                "files": set()
            }
        elif current_commit and line.strip():
            current_commit["files"].add(line.strip())

    if current_commit:
        commits.append(current_commit)

    return list(reversed(commits))

