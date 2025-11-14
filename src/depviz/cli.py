# -*- coding: utf-8 -*-
import argparse, sys
from .config import load_config, print_config
from .pypi_client import PyPIClient
from .graph import DepGraph
from .test_repo import load_test_repo
from .visualize import to_dot
from .errors import ConfigError, FetchError

def stage1(cfg):
    print("[Stage 1] Параметры конфигурации:")
    print_config(cfg)

def stage2(cfg):
    print("[Stage 2] Прямые зависимости для заданного пакета:")
    if cfg.mode != 'real':
        print("Режим test не поддерживает обращение к PyPI для конкретной версии.")
        return
    client = PyPIClient(cfg.repository_url)
    deps = client.get_direct_dependencies_for_version(cfg.package_name, cfg.version)
    if not deps:
        print("(зависимостей не найдено)")
    else:
        for d in deps:
            line = f"- {d.name}"
            if d.spec:
                line += f"  (spec: {d.spec})"
            if d.extras:
                line += f"  [extras: {', '.join(d.extras)}]"
            if d.marker:
                line += f"  ; {d.marker}"
            print(line)

def stage3(cfg, direct_only: bool = False):
    print("[Stage 3] Построение графа зависимостей (DFS без рекурсии)...")
    g = DepGraph()
    if cfg.mode == 'real':
        g.build_real(cfg.package_name, cfg.version, cfg.repository_url, direct_only=direct_only)
    else:
        repo = load_test_repo(cfg.repository_url)
        g.build_test(repo, cfg.package_name, direct_only=direct_only)
    edges_count = sum(len(v) for v in g.adj.values())
    print(f"Вершин: {len(g.nodes)}, рёбер: {edges_count}")
    if g.cycles and not direct_only:
        print("Обнаружены циклы (ребра):", ", ".join(f"{a}->{b}" for a, b in g.cycles))
    print("Прямые зависимости корня:", ", ".join(g.direct_deps(cfg.package_name)) or "(нет)")

def stage4(cfg, show_install_order: bool):
    print("[Stage 4] Дополнительные операции...")
    g = DepGraph()
    if cfg.mode == 'real':
        g.build_real(cfg.package_name, cfg.version, cfg.repository_url, direct_only=False)
    else:
        repo = load_test_repo(cfg.repository_url)
        g.build_test(repo, cfg.package_name, direct_only=False)
    if show_install_order:
        order = g.install_order()
        print("Порядок загрузки (топологический порядок):")
        print(" -> ".join(order))
        if len(order) < len(g.nodes):
            print("[ВНИМАНИЕ] Граф содержит цикл(ы); порядок выведен для ацикличной части.")

def stage5(cfg, direct_only: bool = False):
    print("[Stage 5] Визуализация в формате Graphviz (DOT):")
    g = DepGraph()
    if cfg.mode == 'real':
        g.build_real(cfg.package_name, cfg.version, cfg.repository_url, direct_only=direct_only)
    else:
        repo = load_test_repo(cfg.repository_url)
        g.build_test(repo, cfg.package_name, direct_only=direct_only)
    dot = to_dot(g, cfg.package_name)
    print(dot)

def main():
    ap = argparse.ArgumentParser(
        description="depviz — визуализатор графа зависимостей (pip/PyPI, без сторонних библ.)."
    )
    ap.add_argument('--config', required=True, help='Путь к CSV конфигурации.')
    ap.add_argument('--stage', required=True, type=int, choices=[1, 2, 3, 4, 5], help='Номер этапа (1..5).')
    ap.add_argument(
        '--show-install-order',
        action='store_true',
        help='Этап 4: вывести порядок загрузки зависимостей.'
    )
    ap.add_argument(
        '--direct-only',
        action='store_true',
        help='Использовать только прямые зависимости (без транзитивного обхода, быстрее).'
    )
    args = ap.parse_args()

    try:
        cfg = load_config(args.config)
    except ConfigError as e:
        print(f"[Config error] {e}", file=sys.stderr)
        sys.exit(2)

    if args.stage == 1:
        stage1(cfg)
        return

    try:
        if args.stage == 2:
            stage2(cfg)
        elif args.stage == 3:
            stage3(cfg, direct_only=args.direct_only)
        elif args.stage == 4:
            stage4(cfg, args.show_install_order)
        elif args.stage == 5:
            stage5(cfg, direct_only=args.direct_only)
    except FetchError as e:
        print(f"[Fetch error] {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"[Error] {e}", file=sys.stderr)
        sys.exit(1)
