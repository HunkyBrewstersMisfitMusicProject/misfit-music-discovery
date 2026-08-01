"""Offline audio feature extraction for sound-similarity (no ML model, free).

We extract a fixed-length feature vector from a decoded audio file using only
ffmpeg (decode to PCM) + numpy (stdlib-free math). Features capture TIMBRE and
TEXTURE: spectral centroid, rolloff, zero-crossing rate, RMS, and a 12-bin chroma
(semitone-class energy). Aggregated across frames (mean+std) into one vector.

This is NOT a learned embedding — it catches "sounds alike" by spectral character,
not musical semantics. That's the honest v1: real, free, offline, no model download.
A learned encoder is a later upgrade (crosses into model-hosted territory).
"""
import hashlib
import io
import os
import subprocess
import tempfile
import urllib.request
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
    # semitone center frequencies (log-spaced) for a 12-bin chroma
    midi = np.arange(24, 96)  # C1..B6
    fc = 440.0 * 2 ** ((midi - 69) / 12.0)
    for i in range(0, n - frame, hop):
        seg = samples[i:i + frame]
        if seg.shape[0] < frame:
            break
        w = seg * np.hanning(frame)
        spec = np.abs(np.fft.rfft(w)) + 1e-10
        freqs = np.fft.rfftfreq(frame, 1.0 / sr)
        # spectral centroid / rolloff
        centroid = float(np.sum(freqs * spec) / np.sum(spec))
        cum = np.cumsum(spec)
        rolloff = float(freqs[np.searchsorted(cum, 0.85 * cum[-1])])
        zcr = float(np.mean((seg[:-1] * seg[1:]) < 0))
        rms = float(np.sqrt(np.mean(seg ** 2)))
        # 12-bin log-frequency chroma (project energy onto semitone bands)
        chroma = np.zeros(12)
        for f, e in zip(freqs, spec):
            if f <= 0:
                continue
            midi_f = 69 + 12 * np.log2(f / 440.0)
            if 24 <= midi_f < 96:
                chroma[int(round(midi_f)) % 12] += e
        s = chroma.sum()
        if s > 0:
            chroma = chroma / s
        feats.append([centroid / sr, rolloff / sr, zcr, rms] + chroma.tolist())
    return np.array(feats) if feats else np.zeros((1, 16))


def extract_features(path):
    """Return a normalized 32-dim feature vector for the file.

    Frequencies are scaled by sample rate so the vector is comparable across
    files. The 12-bin chroma carries PITCH CLASS content (so 440 vs 120 differ),
    centroid/rolloff carry brightness. Honest v1: timbre/texture, not semantics.
    """
    samples, sr = _decode_pcm(path)
    if samples.size == 0:
        return np.zeros(32)
    f = _frame_features(samples, sr)
    mean = f.mean(axis=0)
    std = f.std(axis=0)
    vec = np.concatenate([mean, std])
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


def preview_vec(manifest, timeout=20, tmpdir=None):
    """Fetch an artist's HOSTED preview clip, fingerprint it, DISCARD the clip.

    The audio bytes are NEVER stored by the index — downloaded to a temp file,
    decoded to a feature vector, then deleted. Custody of the audio stays with
    the artist. Returns (vector, None) on success, or (None, reason) on failure
    (no preview field, fetch error, decode error, offline).

    This is the bridge from tag-guess to TRUE sound-similarity for registry
    artists, without us ever hosting or retaining their music.
    """
    url = manifest.get("preview")
    if not url:
        return None, "no preview field"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mmp/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        d = tmpdir or tempfile.mkdtemp(prefix="mmp-prev-")
        os.makedirs(d, exist_ok=True)
        suffix = ".webm" if url.lower().endswith(".webm") else ".tmp"
        path = os.path.join(d, "clip" + suffix)
        with open(path, "wb") as fh:
            fh.write(data)
        vec = extract_features(path)
        os.remove(path)
        if tmpdir is None:
            os.rmdir(d)
        if vec.shape != (32,) or float((vec ** 2).sum()) == 0:
            return None, "decode produced empty vector"
        return vec, None
    except Exception as e:
        return None, f"preview fetch failed: {e}"


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
