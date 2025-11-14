# -*- coding: utf-8 -*-
from typing import Dict, Set

def load_test_repo(path: str) -> Dict[str, Set[str]]:
    """Файл с тестовым графом, формат строк:
    A: B C
    B: D
    C: D E
    D:
    E:
    Пустые строки и строки, начинающиеся с #, игнорируются.
    """
    graph: Dict[str, Set[str]] = {}
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if ':' not in line:
                raise ValueError(f"Invalid line (':' expected): {line}")
            name, deps = line.split(':', 1)
            name = name.strip()
            deps = deps.strip()
            dep_names = set()
            if deps:
                for d in deps.split():
                    dep_names.add(d.strip())
            graph.setdefault(name, set()).update(dep_names)
            for d in dep_names:
                graph.setdefault(d, set())
    return graph
