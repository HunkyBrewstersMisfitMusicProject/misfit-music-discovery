"""Command-line entry point for the Misfit Music Project toolkit."""

import argparse
import json
import sys

from . import audio
from . import manifest as manifest_mod
from . import index as index_mod
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
    pm.add_argument("--out", help="write manifest JSON to this path")

    # --- discovery: index ---
    pib = sub.add_parser("index", help="Build/query a local discovery index "
                                      "from an open registry")
    pib.add_argument("--registry",
                     default="file:///home/misfitmusicproject/misfit-music/seed-registry.json",
                     help="registry URL or file:// path (list of manifest URLs)")
    pib.add_argument("--genre", help="filter by genre (substring, ci)")
    pib.add_argument("--location", help="filter by location (substring, ci)")
    pib.add_argument("--name", help="filter by name (substring, ci)")

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
        )
        text = manifest_mod.render_manifest(man, args.out)
        if args.out:
            print(f"wrote manifest -> {args.out}")
        else:
            print(text)
        return 0

    if args.cmd == "index":
        try:
            idx = index_mod.build_index(args.registry)
        except Exception as e:
            print(f"FAILED to build index: {e}", file=sys.stderr)
            return 1
        results = index_mod.query(
            idx, genre=args.genre, location=args.location, name=args.name
        )
        print(f"registry: {idx['registry']}")
        print(f"artists resolved: {len(idx['artists'])}  "
              f"errors: {len(idx['errors'])}")
        if args.genre or args.location or args.name:
            print(f"matching filter: {len(results)}")
        for a in results:
            loc = a.get("location") or "?"
            genres = ", ".join(a.get("genres", []) or []) or "?"
            links = " ".join(l["url"] for l in a.get("links", []))
            print(f"  - {a.get('name')}  [{loc}]  ({genres})")
            if links:
                print(f"      {links}")
        for e in idx["errors"]:
            print(f"  ! error {e['url']}: {e['reason']}", file=sys.stderr)
        return 0

    p.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
