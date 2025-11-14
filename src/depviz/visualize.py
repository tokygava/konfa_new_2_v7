# -*- coding: utf-8 -*-
from .graph import DepGraph

def to_dot(graph: DepGraph, root: str) -> str:
    lines = []
    lines.append('digraph DEP {')
    lines.append('  rankdir=LR;')
    lines.append('  node [shape=box];')
    lines.append(f'  "{root}" [shape=ellipse, style=filled];')
    for a, outs in sorted(graph.adj.items()):
        for b in sorted(outs):
            lines.append(f'  "{a}" -> "{b}";')
    for a, b in graph.cycles:
        lines.append(f'  "{a}" -> "{b}" [color=red];')
    lines.append('}')
    return '\n'.join(lines)
