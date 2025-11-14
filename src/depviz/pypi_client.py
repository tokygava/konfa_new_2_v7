# -*- coding: utf-8 -*-
import io, json, os, urllib.request, urllib.error, zipfile, tarfile
from typing import List
from .errors import FetchError
from .parser import parse_requires_dist, Dependency

class PyPIClient:
    """Минимальный клиент PyPI (pip index) на стандартной библиотеке."""
    def __init__(self, base_url: str = "https://pypi.org"):
        self.base_url = base_url.rstrip('/')
        self._cache_json = {}
        self._cache_requires = {}

    def _get(self, url: str) -> bytes:
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            raise FetchError(f"HTTP {e.code} for {url}")
        except Exception as e:
            raise FetchError(f"Failed to fetch {url}: {e}")

    def _json(self, url: str) -> dict:
        raw = self._get(url)
        try:
            return json.loads(raw.decode('utf-8'))
        except Exception as e:
            raise FetchError(f"Invalid JSON from {url}: {e}")

    def get_json_for_version(self, name: str, version: str) -> dict:
        key = (name.lower(), version)
        if key in self._cache_json:
            return self._cache_json[key]
        url = f"{self.base_url}/pypi/{name}/{version}/json"
        data = self._json(url)
        self._cache_json[key] = data
        return data

    def get_json_latest(self, name: str) -> dict:
        key = (name.lower(), None)
        if key in self._cache_json:
            return self._cache_json[key]
        url = f"{self.base_url}/pypi/{name}/json"
        data = self._json(url)
        self._cache_json[key] = data
        return data

    def _parse_requires_list(self, requires_dist) -> List[Dependency]:
        out: List[Dependency] = []
        if not requires_dist:
            return out
        for item in requires_dist:
            try:
                out.append(parse_requires_dist(item))
            except Exception:
                continue
        return out

    def _extract_requires_from_dist(self, urls_section: list) -> List[Dependency]:
        if not urls_section:
            return []
        sorted_urls = sorted(
            urls_section,
            key=lambda u: 0 if u.get('packagetype') == 'bdist_wheel' else 1
        )
        for u in sorted_urls:
            href = u.get('url')
            if not href:
                continue
            try:
                data = self._get(href)
            except FetchError:
                continue
            requires = self._extract_requires_from_archive_bytes(data, filename=u.get('filename',''))
            if requires:
                return requires
        return []

    def _extract_requires_from_archive_bytes(self, data: bytes, filename: str) -> List[Dependency]:
        if filename.endswith('.whl') or zipfile.is_zipfile(io.BytesIO(data)):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for name in zf.namelist():
                    if name.endswith('/METADATA') and '.dist-info/' in name:
                        meta = zf.read(name).decode('utf-8', errors='replace')
                        return self._parse_requires_from_metadata_text(meta)
        try:
            bio = io.BytesIO(data)
            with tarfile.open(fileobj=bio, mode='r:*') as tf:
                for member in tf.getmembers():
                    base = os.path.basename(member.name)
                    if base in ('PKG-INFO', 'METADATA'):
                        f = tf.extractfile(member)
                        if not f:
                            continue
                        meta = f.read().decode('utf-8', errors='replace')
                        return self._parse_requires_from_metadata_text(meta)
        except tarfile.ReadError:
            pass
        return []

    def _parse_requires_from_metadata_text(self, text: str) -> List[Dependency]:
        deps: List[Dependency] = []
        for line in text.splitlines():
            if line.startswith('Requires-Dist:'):
                value = line.split(':', 1)[1].strip()
                try:
                    deps.append(parse_requires_dist(value))
                except Exception:
                    continue
        return deps

    def get_direct_dependencies_for_version(self, name: str, version: str) -> List[Dependency]:
        key = (name.lower(), version)
        if key in self._cache_requires:
            return self._cache_requires[key]
        data = self.get_json_for_version(name, version)
        requires = self._parse_requires_list(data.get('info', {}).get('requires_dist'))
        if not requires:
            requires = self._extract_requires_from_dist(data.get('urls', []))
        self._cache_requires[key] = requires
        return requires

    def get_direct_dependencies_latest(self, name: str) -> List[Dependency]:
        key = (name.lower(), None)
        if key in self._cache_requires:
            return self._cache_requires[key]
        data = self.get_json_latest(name)
        requires = self._parse_requires_list(data.get('info', {}).get('requires_dist'))
        if not requires:
            requires = self._extract_requires_from_dist(data.get('urls', []))
        self._cache_requires[key] = requires
        return requires
