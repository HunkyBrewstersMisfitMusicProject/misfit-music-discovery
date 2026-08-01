"""Local discovery index built from an OPEN registry of artist manifest URLs.

The registry is just a JSON list of manifest URLs. Anyone can host one for free
(GitHub Pages, IPFS, own site). This module mirrors those manifests into a local,
searchable index. No server we control, no account, no tier, no tracking.

A registry may also point at curator records (listener-aid playlist curators),
so the index serves both artists AND the people who help listeners find them.
"""

import json
import urllib.request

from . import manifest as m

CURATOR_TYPES = {"curator", "playlist-curator"}


def build_index(registry_url, curators_url=None):
    """Fetch a registry JSON (list of manifest URLs) and resolve each manifest.

    If curators_url is given, also resolve curator records into the index.
    Returns a dict: {artists: [...], curators: [...], errors: [...], registry}
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
        except Exception as e:  # one bad entry is non-fatal
            errors.append({"url": url, "reason": str(e)})

    curators = []
    if curators_url:
        try:
            cdata = _fetch(curators_url)
            clist = json.loads(cdata)
            if isinstance(clist, list):
                curators = [c for c in clist if isinstance(c, dict)]
            elif isinstance(clist, dict):
                curators = [clist]
        except Exception as e:
            errors.append({"url": curators_url, "reason": str(e)})

    return {
        "registry": registry_url,
        "curators_registry": curators_url,
        "artists": artists,
        "curators": curators,
        "errors": errors,
    }


def query(index, genre=None, location=None, name=None, curator=None, limit=20):
    """Filter resolved artists/curators. Case-insensitive substring matches."""
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

    results = [a for a in out if matches(a)][:limit]

    if curator:
        c = curator.lower()
        results = [x for x in index.get("curators", [])
                   if c in (x.get("name") or "").lower()]
    return results


def _fetch(url):
    # Accept bare file paths (hand-authored registries) as file:// URLs.
    if "://" not in url:
        url = "file://" + url
    req = urllib.request.Request(url, headers={"User-Agent": "mmp/0.1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")
