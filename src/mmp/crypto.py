"""Artist identity + payment via ed25519 (trust-by-crypto, no central authority).

Signing is OFFLINE and FREE. An artist owns a private key; their manifest is
signed. A registry accepts a manifest only if its signature verifies against a
published public key. No platform, no gatekeeper, no chain fees.

OPTIONAL payment field (Lightning invoice or crypto address) lets a listener
pay the artist DIRECTLY via the artist's own link — Misfit Music touches no
money and takes no cut. This is the only crypto in scope: a direct artist
payment rail, not a reward/utility token. No listener reward token.

Design constraints honored:
- $0: ed25519 is stdlib-grade, no gas, no chain needed.
- Better-off: artist earns directly; listener pays directly; we skim nothing.
- Non-extractive: signatures prevent impersonation/forgery; payment goes to artist.
"""

import base64
import hashlib
import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _unb64(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def new_key():
    """Generate an ed25519 keypair. Returns (private_pem_str, public_pem_str)."""
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    pub = priv.public_key()
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return priv_pem, pub_pem


def _canonical(manifest: dict) -> bytes:
    """Stable signing payload: the manifest WITHOUT signature fields."""
    signed = {k: v for k, v in manifest.items()
              if k not in ("signature", "public_key")}
    return json.dumps(signed, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_manifest(manifest: dict, private_pem: str) -> dict:
    """Return a copy of manifest with signature + public_key attached."""
    priv = serialization.load_pem_private_key(
        private_pem.encode("ascii"), password=None)
    if not isinstance(priv, Ed25519PrivateKey):
        raise ValueError("private key is not ed25519")
    payload = _canonical(manifest)
    sig = priv.sign(payload)
    pub = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    out = dict(manifest)
    out["public_key"] = _b64(pub.encode("ascii"))
    out["signature"] = _b64(sig)
    return out


def verify_manifest(manifest: dict) -> bool:
    """True iff signature present and valid for the (unsigned) payload."""
    sig_b64 = manifest.get("signature")
    key_b64 = manifest.get("public_key")
    if not sig_b64 or not key_b64:
        return False
    try:
        pub_pem = _unb64(key_b64).decode("ascii")
        pub = serialization.load_pem_public_key(pub_pem.encode("ascii"))
        if not isinstance(pub, Ed25519PublicKey):
            return False
        payload = _canonical(manifest)
        pub.verify(_unb64(sig_b64), payload)
        return True
    except Exception:
        return False


def fingerprint(manifest: dict) -> str:
    """Stable identity hash of an artist's signed manifest (for dedup)."""
    key = manifest.get("public_key") or manifest.get("name", "")
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
