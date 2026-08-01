"""Command-line entry point for the Misfit Music Project toolkit."""

import argparse
import json
import os
import sys

from . import audio
from . import manifest as manifest_mod
from . import index as index_mod
from . import audio_features as af
from . import crypto as crypto_mod
from . import __version__


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="mmp",
        description="Misfit Music Project — free, offline audio + discovery toolkit",
    )
    p.add_argument("--version", action="version", version=f"mmp {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    # --- audio ---
    pi = sub.add_parser("inspect", help="Probe audio/media file metadata")
    pi.add_argument("path", help="file to inspect")

    pt = sub.add_parser("tone", help="Synthesize a test tone via ffmpeg")
    pt.add_argument("out", help="output .wav path")
    pt.add_argument("--seconds", type=float, default=2.0)
    pt.add_argument("--freq", type=float, default=440.0)

    # --- discovery: manifest ---
    pm = sub.add_parser("manifest", help="Generate a portable artist manifest")
    pm.add_argument("--name", required=True, help="artist / project name")
    pm.add_argument("--location", help="city, region")
    pm.add_argument("--genre", action="append", dest="genres",
                    help="repeatable, e.g. --genre ambient --genre experimental")
    pm.add_argument("--bio", help="short self-description")
    pm.add_argument("--link", action="append", dest="links",
                    help="repeatable URL of existing presence "
                         "(Bandcamp/SoundCloud/own site). We mirror it.")
    pm.add_argument("--contact", help="contact email or handle")
    pm.add_argument("--payment", help="OPTIONAL direct artist payment rail: a "
                    "Lightning invoice or crypto address. Listener pays the "
                    "artist DIRECTLY; Misfit Music takes no cut, hosts nothing.")
    pm.add_argument("--preview", help="OPTIONAL URL to an artist-hosted short "
                    "preview clip. Used for TRUE sound-similarity matching. "
                    "Fetched transiently, never stored by the index.")
    pm.add_argument("--key", help="ed25519 private key (PEM) to SIGN the manifest "
                    "(trust-by-crypto). Without it, manifest is unsigned.")
    pm.add_argument("--out", help="write manifest JSON to this path")

    # --- discovery: index ---
    pib = sub.add_parser("index", help="Build/query a local discovery index "
                                      "from an open registry")
    pib.add_argument("--registry",
                     default="file:///home/misfitmusicproject/misfit-music/seed-registry.json",
                     help="registry URL or file:// path (list of manifest URLs)")
    pib.add_argument("--curators",
                     default="file:///home/misfitmusicproject/misfit-music/seed/curators.json",
                     help="curators URL or file:// path (list of curator records)")
    pib.add_argument("--genre", help="filter by genre (substring, ci)")
    pib.add_argument("--location", help="filter by location (substring, ci)")
    pib.add_argument("--name", help="filter by name (substring, ci)")
    pib.add_argument("--curator", help="filter by curator name (substring, ci)")
    pib.add_argument("--verify-sigs", action="store_true",
                     help="drop manifests whose signature is missing/invalid "
                          "(trust-by-crypto). Default: keep all.")
    pib.add_argument("--no-verify", dest="verify_sigs", action="store_false")

    # --- listener: library (profile a local music folder) ---
    pl = sub.add_parser("library", help="Profile a local music folder by sound")
    pl.add_argument("folder", help="path to local audio files")
    pl.add_argument("--out", help="write library profile JSON to this path")

    # --- listener: similar (sound-match a track to registry artists) ---
    ps = sub.add_parser("similar", help="Find registry artists whose SOUND "
                                      "matches a reference track")
    ps.add_argument("track", help="reference audio file (your local track)")
    ps.add_argument("--registry",
                    default="file:///home/misfitmusicproject/misfit-music/seed-registry.json",
                    help="registry URL or file:// path")
    ps.add_argument("--top", type=int, default=5, help="how many to return")

    # --- listener: export (portable playlist of matched artists) ---
    pe = sub.add_parser("export", help="Export matched artists as a portable "
                                      "playlist to import into YOUR service")
    pe.add_argument("track", help="reference audio file")
    pe.add_argument("--registry",
                    default="file:///home/misfitmusicproject/misfit-music/seed-registry.json",
                    help="registry URL or file:// path")
    pe.add_argument("--service", default="generic",
                    choices=["generic", "m3u", "csv"],
                    help="export format (generic=JSON+M3U+CSV, all host-neutral)")
    pe.add_argument("--top", type=int, default=10)
    pe.add_argument("--out", required=True, help="output base path (no ext)")

    # --- crypto: identity (trust-by-crypto) ---
    psg = sub.add_parser("sign", help="Sign a manifest file with your ed25519 key")
    psg.add_argument("manifest", help="manifest JSON file (modified in place)")
    psg.add_argument("--key", required=True, help="ed25519 private key PEM")

    pv = sub.add_parser("verify", help="Verify a manifest's signature")
    pv.add_argument("manifest", help="manifest JSON file")

    # --- crypto: keygen ---
    pkg = sub.add_parser("keygen", help="Generate an ed25519 keypair (PEM)")
    pkg.add_argument("--out", help="write priv+pub PEM to this base path")

    args = p.parse_args(argv)

    if args.cmd == "inspect":
        info = audio.probe(args.path)
        print(json.dumps(info, indent=2))
        return 0 if info.get("ok") else 1

    if args.cmd == "tone":
        ok = audio.synth_tone(args.out, args.seconds, args.freq)
        if ok:
            print(f"wrote {args.out} ({args.seconds}s @ {args.freq}Hz)")
            return 0
        print(f"FAILED to write {args.out}", file=sys.stderr)
        return 1

    if args.cmd == "manifest":
        man = manifest_mod.make_manifest(
            name=args.name,
            location=args.location,
            genres=args.genres or [],
            bio=args.bio,
            links=args.links or [],
            contact=args.contact,
            payment=args.payment,
            preview=args.preview,
        )
        if args.key:
            try:
                key_text = args.key
                if os.path.exists(args.key):
                    with open(args.key, encoding="utf-8") as kf:
                        key_text = kf.read()
                man = crypto_mod.sign_manifest(man, key_text)
                print("manifest SIGNED (trust-by-crypto).")
            except Exception as e:
                print(f"FAILED to sign: {e}", file=sys.stderr)
                return 1
        text = manifest_mod.render_manifest(man, args.out)
        if args.out:
            print(f"wrote manifest -> {args.out}")
        else:
            print(text)
        return 0

    if args.cmd == "index":
        try:
            idx = index_mod.build_index(args.registry, args.curators)
        except Exception as e:
            print(f"FAILED to build index: {e}", file=sys.stderr)
            return 1
        artists = idx["artists"]
        dropped = 0
        if args.verify_sigs:
            kept = []
            for a in artists:
                if crypto_mod.verify_manifest(a):
                    kept.append(a)
                else:
                    dropped += 1
            artists = kept
        results = index_mod.query(
            {**idx, "artists": artists}, genre=args.genre, location=args.location,
            name=args.name, curator=args.curator,
        )
        print(f"registry: {idx['registry']}")
        print(f"artists resolved: {len(artists)}  "
              f"curators: {len(idx['curators'])}  "
              f"errors: {len(idx['errors'])}"
              + (f"  unsigned/invalid dropped: {dropped}" if args.verify_sigs else ""))
        if args.curator:
            for c in results:
                pls = "  ".join(f"{p['title']} -> {p['url']}"
                                for p in c.get("playlists", []))
                print(f"  - CURATOR {c.get('name')}: {c.get('blurb')}")
                if pls:
                    print(f"      {pls}")
        else:
            if args.genre or args.location or args.name:
                print(f"matching filter: {len(results)}")
            for a in results:
                loc = a.get("location") or "?"
                genres = ", ".join(a.get("genres", []) or []) or "?"
                links = " ".join(l["url"] for l in a.get("links", []))
                pay = f"  [pay: {a['payment']}]" if a.get("payment") else ""
                print(f"  - {a.get('name')}  [{loc}]  ({genres}){pay}")
                if links:
                    print(f"      {links}")
        for e in idx["errors"]:
            print(f"  ! error {e['url']}: {e['reason']}", file=sys.stderr)
        return 0

    if args.cmd == "sign":
        try:
            with open(args.manifest, encoding="utf-8") as fh:
                man = json.load(fh)
            key_text = args.key
            if os.path.exists(args.key):
                with open(args.key, encoding="utf-8") as kf:
                    key_text = kf.read()
            signed = crypto_mod.sign_manifest(man, key_text)
            with open(args.manifest, "w", encoding="utf-8") as fh:
                json.dump(signed, fh, indent=2)
            print(f"signed -> {args.manifest}")
            return 0
        except Exception as e:
            print(f"FAILED sign: {e}", file=sys.stderr)
            return 1

    if args.cmd == "verify":
        try:
            with open(args.manifest, encoding="utf-8") as fh:
                man = json.load(fh)
            ok = crypto_mod.verify_manifest(man)
            print(f"{'VALID' if ok else 'INVALID'} signature: {args.manifest}")
            return 0 if ok else 1
        except Exception as e:
            print(f"FAILED verify: {e}", file=sys.stderr)
            return 1

    if args.cmd == "keygen":
        try:
            priv, pub = crypto_mod.new_key()
            if args.out:
                with open(args.out + ".pem", "w") as fh:
                    fh.write(priv)
                with open(args.out + ".pub.pem", "w") as fh:
                    fh.write(pub)
                print(f"wrote {args.out}.pem + {args.out}.pub.pem (KEEP PRIVATE KEY SECRET)")
            else:
                print(priv)
                print(pub)
            return 0
        except Exception as e:
            print(f"FAILED keygen: {e}", file=sys.stderr)
            return 1

    if args.cmd == "library":
        try:
            vecs = {}
            for root, _, files in os.walk(args.folder):
                for fn in files:
                    if fn.lower().endswith((".wav", ".mp3", ".flac", ".ogg")):
                        fp = os.path.join(root, fn)
                        try:
                            vecs[fp] = af.extract_features(fp)
                        except Exception as ex:
                            print(f"  ! skip {fp}: {ex}", file=sys.stderr)
            if not vecs:
                print("No audio files found / decoded.", file=sys.stderr)
                return 1
            # library profile = mean vector over its tracks
            mean_vec = af.mean_vectors(list(vecs.values()))
            profile = {
                "folder": args.folder,
                "tracks": len(vecs),
                "profile_vector": mean_vec.tolist(),
            }
            if args.out:
                with open(args.out, "w", encoding="utf-8") as fh:
                    json.dump(profile, fh, indent=2)
                print(f"wrote library profile -> {args.out} ({len(vecs)} tracks)")
            else:
                print(json.dumps(profile, indent=2))
            return 0
        except Exception as e:
            print(f"FAILED library: {e}", file=sys.stderr)
            return 1

    if args.cmd == "similar":
        try:
            ref = af.extract_features(args.track)
            idx = index_mod.build_index(args.registry)
            items = [(a["name"], af.artist_vec(a)) for a in idx["artists"]]
            ranked = af.rank_by_similarity(ref, items)[: args.top]
            print(f"reference: {args.track}")
            print(f"sound-similar artists (timbre/texture match):")
            for name, score in ranked:
                a = next(x for x in idx["artists"] if x["name"] == name)
                links = " ".join(l["url"] for l in a.get("links", []))
                print(f"  - {name}  [score {score:.3f}]  {links}")
            return 0
        except Exception as e:
            print(f"FAILED similar: {e}", file=sys.stderr)
            return 1

    if args.cmd == "export":
        try:
            ref = af.extract_features(args.track)
            idx = index_mod.build_index(args.registry)
            items = [(a["name"], af.artist_vec(a)) for a in idx["artists"]]
            ranked = af.rank_by_similarity(ref, items)[: args.top]
            entries = []
            for name, score in ranked:
                a = next(x for x in idx["artists"] if x["name"] == name)
                entries.append({
                    "name": name,
                    "score": round(score, 3),
                    "location": a.get("location"),
                    "links": a.get("links", []),
                })
            # generic JSON
            with open(args.out + ".json", "w", encoding="utf-8") as fh:
                json.dump({"source_track": args.track, "artists": entries},
                          fh, indent=2)
            # M3U (host-neutral: points to artist's OWN links, not our hosting)
            with open(args.out + ".m3u", "w", encoding="utf-8") as fh:
                fh.write("#EXTM3U\n")
                for e in entries:
                    url = (e["links"][0]["url"] if e["links"] else "")
                    fh.write(f"#EXTINF:-1,{e['name']}\n{url}\n")
            # CSV for importers (Soundiiz/TuneMyMusic-style)
            with open(args.out + ".csv", "w", encoding="utf-8") as fh:
                fh.write("artist,score,location,link\n")
                for e in entries:
                    url = (e["links"][0]["url"] if e["links"] else "")
                    fh.write(f"{e['name']},{e['score']},{e['location'] or ''},{url}\n")
            print(f"exported {len(entries)} artists -> {args.out}.(json|m3u|csv)")
            print("Import the .m3u or .csv into YOUR service. We host nothing.")
            return 0
        except Exception as e:
            print(f"FAILED export: {e}", file=sys.stderr)
            return 1

    p.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
