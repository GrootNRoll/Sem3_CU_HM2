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


def find_dependencies(commits):
    """
    Определяет зависимости между коммитами на основе измененных файлов.
    """
    dependencies = defaultdict(list)

    for i, current_commit in enumerate(commits):
        for j in range(i):
            previous_commit = commits[j]
            # Если коммиты изменяют одинаковые файлы, создаем зависимость
            if not current_commit["files"].isdisjoint(previous_commit["files"]):
                dependencies[i].append(j)

    return dependencies


def resolve_transitive_dependencies(direct_dependencies):
    """
    Убирает транзитивные зависимости, оставляя только прямые.
    """
    reduced_dependencies = defaultdict(list)

    for node, deps in direct_dependencies.items():
        # Для каждого узла проверяем, какие зависимости не являются транзитивными
        non_transitive_deps = set(deps)
        for dep in deps:
            non_transitive_deps -= set(direct_dependencies.get(dep, []))  # Убираем транзитивные зависимости
        reduced_dependencies[node] = list(non_transitive_deps)

    return reduced_dependencies


def generate_mermaid_graph(commits, dependencies):
    """
    Генерирует граф Mermaid с учетом транзитивных зависимостей.
    """
    graph = ["graph TD"]

    for i, commit in enumerate(commits):
        node_id = f"commit_{i}"
        file_list = "<br>".join(commit["files"]) if commit["files"] else "No changes"
        graph.append(f"    {node_id}[\"{commit['hash']}<br>{commit['date']}<br>{file_list}\"]")

        # Добавляем зависимости
        for dep in dependencies.get(i, []):
            dep_node_id = f"commit_{dep}"
            graph.append(f"    {dep_node_id} --> {node_id}")

    return "\n".join(graph)
