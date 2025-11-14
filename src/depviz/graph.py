# -*- coding: utf-8 -*-
from typing import Dict, Set, List, Tuple
from collections import deque, defaultdict
from .pypi_client import PyPIClient
from .parser import Dependency

class DepGraph:
    def __init__(self):
        self.adj: Dict[str, Set[str]] = defaultdict(set)
        self.nodes: Set[str] = set()
        self.cycles: List[Tuple[str, str]] = []

    def add_edge(self, a: str, b: str):
        self.nodes.add(a)
        self.nodes.add(b)
        self.adj[a].add(b)
        self.adj.setdefault(b, set())

    def build_real(self, root_name: str, root_version: str, base_url: str, direct_only: bool = False):
        client = PyPIClient(base_url)
        root_deps = client.get_direct_dependencies_for_version(root_name, root_version)
        for d in root_deps:
            self.add_edge(root_name, d.name)
        if direct_only:
            return
        color: Dict[str, int] = {n: 0 for n in self.nodes}  # 0=unseen,1=visiting,2=done
        stack: List[str] = [root_name]
        while stack:
            v = stack.pop()
            state = color.get(v, 0)
            if state == 0:
                color[v] = 1
                stack.append(v)
                if v == root_name:
                    deps = root_deps
                else:
                    try:
                        deps = client.get_direct_dependencies_latest(v)
                    except Exception:
                        deps = []
                for d in deps:
                    u = d.name
                    self.add_edge(v, u)
                    c = color.get(u, 0)
                    if c == 0:
                        stack.append(u)
                    elif c == 1:
                        self.cycles.append((v, u))
            elif state == 1:
                color[v] = 2

    def build_test(self, graph: Dict[str, Set[str]], root: str, direct_only: bool = False):
        self.nodes.update(graph.keys())
        if direct_only:
            for u in graph.get(root, set()):
                self.add_edge(root, u)
            return
        color: Dict[str, int] = {n: 0 for n in graph.keys()}
        stack: List[str] = [root]
        while stack:
            v = stack.pop()
            state = color.get(v, 0)
            if state == 0:
                color[v] = 1
                stack.append(v)
                for u in graph.get(v, set()):
                    self.add_edge(v, u)
                    c = color.get(u, 0)
                    if c == 0:
                        stack.append(u)
                    elif c == 1:
                        self.cycles.append((v, u))
            elif state == 1:
                color[v] = 2

    def direct_deps(self, name: str) -> List[str]:
        return sorted(self.adj.get(name, set()))

    def install_order(self) -> List[str]:
        indeg = {n: 0 for n in self.nodes}
        for a, outs in self.adj.items():
            for b in outs:
                indeg[b] += 1
        q = deque(sorted([n for n, d in indeg.items() if d == 0]))
        order: List[str] = []
        while q:
            v = q.popleft()
            order.append(v)
            for u in sorted(self.adj.get(v, set())):
                indeg[u] -= 1
                if indeg[u] == 0:
                    q.append(u)
        return order
