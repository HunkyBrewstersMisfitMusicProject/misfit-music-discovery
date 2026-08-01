"""Command-line entry point for the Misfit Music Project toolkit."""

import argparse
import json
import sys

from . import audio
from . import __version__


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="mmp",
        description="Misfit Music Project — free, offline audio toolkit",
    )
    p.add_argument("--version", action="version",
                   version=f"mmp {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("inspect", help="Probe audio/media file metadata")
    pi.add_argument("path", help="file to inspect")

    pt = sub.add_parser("tone", help="Synthesize a test tone via ffmpeg")
    pt.add_argument("out", help="output .wav path")
    pt.add_argument("--seconds", type=float, default=2.0)
    pt.add_argument("--freq", type=float, default=440.0)

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

    p.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
