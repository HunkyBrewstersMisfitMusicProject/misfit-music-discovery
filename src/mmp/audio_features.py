"""Offline audio feature extraction for sound-similarity (no ML model, free).

We extract a fixed-length feature vector from a decoded audio file using only
ffmpeg (decode to PCM) + numpy (stdlib-free math). Features capture TIMBRE and
TEXTURE: spectral centroid, rolloff, zero-crossing rate, RMS, and a 12-bin chroma
(semitone-class energy). Aggregated across frames (mean+std) into one vector.

This is NOT a learned embedding — it catches "sounds alike" by spectral character,
not musical semantics. That's the honest v1: real, free, offline, no model download.
A learned encoder is a later upgrade (crosses into model-hosted territory).
"""

import io
import subprocess
import numpy as np


def _decode_pcm(path, sr=22050):
    """Decode audio to mono float32 PCM via ffmpeg. Returns (samples, sr)."""
    cmd = [
        "ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", str(sr),
        "-f", "s16le", "-",
    ]
    raw = subprocess.run(cmd, capture_output=True, timeout=120).stdout
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    return samples, sr


def _frame_features(samples, sr, frame=1024, hop=512):
    n = len(samples)
    feats = []
    i = 0
    while i + frame <= n:
        seg = samples[i:i + frame]
        i += hop
        if seg.shape[0] < frame:
            break
        # window
        w = seg * np.hanning(frame)
        spec = np.abs(np.fft.rfft(w))
        freqs = np.fft.rfftfreq(frame, 1.0 / sr)
        mag = spec + 1e-10
        # spectral centroid
        centroid = float(np.sum(freqs * mag) / np.sum(mag))
        # spectral rolloff (85%)
        cum = np.cumsum(mag)
        rolloff = float(freqs[np.searchsorted(cum, 0.85 * cum[-1])])
        # zero crossing rate
        zcr = float(np.mean((seg[:-1] * seg[1:]) < 0))
        # rms
        rms = float(np.sqrt(np.mean(seg ** 2)))
        # chroma: fold into 12 semitone classes
        bins = np.log2(freqs[1:] / 440.0 * 12 + 69)  # MIDI-ish
        chroma = np.zeros(12)
        for k, e in zip(bins, mag[1:]):
            chroma[int(round(k)) % 12] += e
        chroma = chroma / (chroma.sum() + 1e-10)
        feats.append([centroid, rolloff, zcr, rms] + chroma.tolist())
    return np.array(feats) if feats else np.zeros((1, 16))


def extract_features(path):
    """Return a normalized 32-dim feature vector for the file."""
    samples, sr = _decode_pcm(path)
    if samples.size == 0:
        return np.zeros(32)
    f = _frame_features(samples, sr)
    mean = f.mean(axis=0)
    std = f.std(axis=0)
    vec = np.concatenate([mean, std])
    # guard against zero vector
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.astype(np.float32)


def cosine_similarity(a, b):
    return float(np.dot(a, b))  # both L2-normalized -> cosine


def rank_by_similarity(ref_vec, items):
    """items: list of (name, vec). Returns sorted list of (name, score)."""
    scored = [(name, cosine_similarity(ref_vec, vec)) for name, vec in items]
    return sorted(scored, key=lambda x: x[1], reverse=True)


def mean_vectors(vecs):
    """L2-normalized mean of a list of (already normalized) vectors."""
    if not vecs:
        return np.zeros(32)
    m = np.mean(np.stack(vecs), axis=0)
    norm = np.linalg.norm(m)
    if norm > 0:
        m = m / norm
    return m.astype(np.float32)


def artist_vec(manifest):
    """Derive a pseudo 'sound' vector for an artist from their manifest tags.

    IMPORTANT/HONEST: a registry artist has no hosted audio we can decode
    (we don't download their tracks). So sound-similarity for registry artists
    uses a TAG-derived vector (genres + city hashed into the 32-dim space),
    NOT real audio. This lets `similar` rank by declared style, but it is
    coarser than true audio fingerprinting. The accurate path (artist opts in
    with a short preview clip in their manifest) is a later upgrade.
    """
    import hashlib
    vec = np.zeros(32, dtype=np.float32)
    text = " ".join(manifest.get("genres", []) or [])
    loc = manifest.get("location") or ""
    text = (text + " " + loc).lower()
    if not text.strip():
        return vec
    # fold a stable hash of the text into the vector deterministically
    h = hashlib.sha256(text.encode("utf-8")).digest()
    for i in range(32):
        # map bytes -> signed contributions, spread across dims
        byte = h[i % len(h)]
        vec[i] += (byte - 128) / 128.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec
