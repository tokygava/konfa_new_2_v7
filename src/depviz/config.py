# -*- coding: utf-8 -*-
import csv, os, re
from dataclasses import dataclass
from .errors import ConfigError

_NAME_RE = re.compile(r'^[A-Za-z0-9_.-]+$')

@dataclass
class Config:
    package_name: str
    repository_url: str
    mode: str     # 'real' | 'test'
    version: str

def _read_csv_kv(path: str) -> dict:
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")
    raw = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 2:
                continue
            k = (row[0] or '').strip()
            v = (row[1] or '').strip()
            if not k:
                continue
            # возможный заголовок
            if k.lower() == 'key' and v.lower() in ('value', ''):
                continue
            raw[k] = v
    return raw

def load_config(path: str) -> Config:
    data = _read_csv_kv(path)
    required = ['package_name', 'repository_url', 'mode', 'version']
    missing = [k for k in required if k not in data or not data[k]]
    if missing:
        raise ConfigError(f"Missing config keys: {', '.join(missing)} (in {path})")

    package_name = data['package_name'].strip()
    if not _NAME_RE.match(package_name):
        raise ConfigError(f"Invalid package_name: {package_name!r}")

    mode = data['mode'].strip().lower()
    if mode not in ('real', 'test'):
        raise ConfigError(f"Invalid mode: {mode!r} (expected 'real' or 'test')")

    repository_url = data['repository_url'].strip()
    if mode == 'real':
        if not (repository_url.startswith('https://') or repository_url.startswith('http://')):
            raise ConfigError("In 'real' mode repository_url must be an HTTP(S) URL (PyPI index).")
        if 'github.com' in repository_url.lower():
            raise ConfigError("GitHub is not a package index. Use https://pypi.org (pip).")
    else:
        # test mode: repository_url is a path to local file
        if not os.path.exists(repository_url):
            raise ConfigError(f"Test repo file does not exist: {repository_url}")

    version = data['version'].strip()
    if not version or any(c.isspace() for c in version):
        raise ConfigError(f"Invalid version: {version!r}")

    return Config(
        package_name=package_name,
        repository_url=repository_url,
        mode=mode,
        version=version,
    )

def print_config(cfg: Config):
    pairs = {
        'package_name': cfg.package_name,
        'repository_url': cfg.repository_url,
        'mode': cfg.mode,
        'version': cfg.version,
    }
    for k, v in pairs.items():
        print(f"{k}={v}")
