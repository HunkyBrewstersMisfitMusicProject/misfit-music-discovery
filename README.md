# Misfit Music Project — Open Discovery Index

A free, open, **non-tiered** discovery layer for independent artists. The protocol
is the product, not the platform: artists own their manifests, listeners browse
without accounts or tracking, and nobody pays to be found.

## Live (published)
https://hunkybrewstersmisfitmusicproject.github.io/misfit-music-discovery/

- `registry.json` — list of manifest URLs (relative, portable)
- `*.json` — mirrored artist manifests (artist-owned)
- `curators.json` — listener-aid playlist curators (e.g. Hunky Brewster)
- `index.html` — zero-dependency search viewer

## How it works
1. An artist runs `python -m mmp.cli manifest --name ... --link <their bandcamp/etc>`
   to generate a portable manifest. They host it anywhere (own site, IPFS, Pages).
2. The manifest URL is added to `seed-registry.json` (or any registry).
3. `python scripts/build_site.py` regenerates `gh-pages/`.
4. `bash scripts/publish.sh` pushes to GitHub Pages (needs `gh` auth).

No tiers, no cost, no account required to be discovered or to discover.

## Local toolkit
```
python -m mmp.cli index --location Portland
python -m mmp.cli index --curator Hunky
python -m mmp.cli manifest --name "My Act" --link https://myact.bandcamp.com
```

## Status
- [x] Offline `mmp` toolkit (tone, inspect, manifest, index)
- [x] Open registry + curator model
- [x] Static GitHub Pages site (live URL above)
- [ ] Real artist onboarding beyond seed data
- [ ] Listener-side `similar` / library-bridging command
- [ ] Mirror existing artist presence automatically (Bandcamp/SoundCloud ingest)

All tooling is free and local. Budget spent: $0.
