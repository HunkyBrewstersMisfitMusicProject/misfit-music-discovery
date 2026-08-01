"""Local discovery index built from an OPEN registry of artist manifest URLs.

The registry is just a JSON list of manifest URLs. Anyone can host one for free
(GitHub Pages, IPFS, own site). This module mirrors those manifests into a local,
searchable index. No server we control, no account, no tier, no tracking.
"""

import json
import urllib.request

from . import manifest as m


def build_index(registry_url):
    """Fetch a registry JSON (list of manifest URLs) and resolve each manifest.

    Returns a dict: {artists: [...], errors: [...], registry: url}
    """
    raw = _fetch(registry_url)
    urls = json.loads(raw)
    if not isinstance(urls, list):
        raise ValueError("registry must be a JSON list of manifest URLs")

    artists = []
    errors = []
    for url in urls:
        try:
            data = _fetch(url)
            obj = json.loads(data)
            if m.is_manifest(obj):
                artists.append(obj)
            else:
                errors.append({"url": url, "reason": "not a manifest"})
        except Exception as e:  # network/parse failure on one entry is non-fatal
            errors.append({"url": url, "reason": str(e)})

    return {"registry": registry_url, "artists": artists, "errors": errors}


def query(index, genre=None, location=None, name=None, limit=20):
    """Filter the resolved artists. All matches are case-insensitive substring."""
    out = index.get("artists", [])

    def matches(a):
        if genre:
            g = genre.lower()
            if not any(g in (x or "").lower() for x in a.get("genres", [])):
                return False
        if location:
            l = location.lower()
            if l not in (a.get("location") or "").lower():
                return False
        if name:
            n = name.lower()
            if n not in (a.get("name") or "").lower():
                return False
        return True

    return [a for a in out if matches(a)][:limit]


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "mmp/0.1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")
