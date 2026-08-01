"""Artist Manifest: a portable, self-describing record for independent artists.

A manifest is plain JSON owned by the artist. It is NOT stored on any server we
control, requires no account, and costs nothing to publish or read. The artist
self-describes; the discovery index only mirrors it. This is the "no tiers" guarantee
enforced by architecture, not by a pricing promise.
"""

import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

MANIFEST_VERSION = "0.1.0"

# Known link "kinds" we can ingest. Open — artists can add any key.
KNOWN_KINDS = {
    "bandcamp": "bandcamp",
    "soundcloud": "soundcloud",
    "spotify": "spotify",
    "youtube": "youtube",
    "instagram": "instagram",
    "tiktok": "tiktok",
    "site": "website",
    "email": "email",
}


def _classify_link(url):
    """Best-effort kind from a URL. Falls back to 'other'."""
    if url.startswith("mailto:"):
        return "email"
    host = (urlparse(url).netloc or "").lower()
    for key in KNOWN_KINDS:
        if key in host:
            return KNOWN_KINDS[key]
    return "other"


def make_manifest(name, location=None, genres=None, bio=None, links=None,
                  contact=None):
    """Build a manifest dict from an artist's existing footprint.

    `links` may be a list of URLs or list of (kind, url) tuples. This is the
    cold-start answer: artists paste their EXISTING presence and we mirror it.
    """
    genres = genres or []
    links = links or []
    normalized = []
    for item in links:
        if isinstance(item, (list, tuple)):
            kind, url = item[0], item[1]
        else:
            kind, url = _classify_link(item), item
        normalized.append({"kind": kind, "url": url})

    return {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "location": location,
        "genres": genres,
        "bio": bio,
        "contact": contact,
        "links": normalized,
        # Empty by default: the artist fills these from their own feeds; we do
        # not invent release data. Keeps the manifest honest.
        "releases": [],
        "owner_note": (
            "This manifest is owned by the artist. Host it anywhere "
            "(own site, GitHub Pages, IPFS). No account, no tier, no cost."
        ),
    }


def render_manifest(manifest, path=None):
    """Serialize a manifest. If path given, write it; else return the string."""
    text = json.dumps(manifest, indent=2, ensure_ascii=False)
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return text


def load_manifest(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def is_manifest(obj):
    return isinstance(obj, dict) and obj.get("manifest_version") is not None
