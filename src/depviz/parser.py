# -*- coding: utf-8 -*-
"""Мини-парсер строк Requires-Dist (PEP 508-лайт)."""
import re
from dataclasses import dataclass
from typing import List, Optional

_REQ_RE = re.compile(
    r"^\s*"
    r"(?P<name>[A-Za-z0-9_.-]+)"
    r"(?:\s*\[(?P<extras>[^\]]+)\])?"
    r"(?:\s*\((?P<spec>[^\)]+)\))?"
    r"(?:\s*;\s*(?P<marker>.+))?"
    r"\s*$"
)

@dataclass(frozen=True)
class Dependency:
    name: str
    spec: Optional[str] = None
    marker: Optional[str] = None
    extras: Optional[List[str]] = None

def parse_requires_dist(s: str) -> Dependency:
    m = _REQ_RE.match(s)
    if not m:
        # fallback — попытка отделить имя от спецификатора версии по операторам
        name, spec = _split_name_spec_fallback(s)
        return Dependency(name=name, spec=spec or None, marker=None, extras=None)
    name = m.group('name')
    extras = m.group('extras')
    spec = m.group('spec')
    marker = m.group('marker')
    extras_list = [e.strip() for e in extras.split(',')] if extras else None
    return Dependency(
        name=name,
        spec=spec.strip() if spec else None,
        marker=marker.strip() if marker else None,
        extras=extras_list,
    )

_COMPARATORS = ['===', '==', '!=', '>=', '<=', '>', '<', '~=']

def _split_name_spec_fallback(s: str):
    idx = len(s)
    for comp in _COMPARATORS:
        pos = s.find(comp)
        if pos != -1:
            idx = min(idx, pos)
    name = s[:idx].strip().rstrip(',')
    spec = s[idx:].strip() or None
    if spec and ';' in spec:
        spec, _marker = spec.split(';', 1)
        spec = spec.strip()
    if '[' in name and ']' in name:
        base = name[:name.index('[')]
        name = base.strip()
    return name, spec
