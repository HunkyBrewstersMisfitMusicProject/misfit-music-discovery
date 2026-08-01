# GitHub Pages publish target

This directory is the build output of `scripts/build_site.py`. It contains a
fully static, dependency-free open discovery index:

- `registry.json` — list of manifest URLs (relative)
- `*.json` — mirrored artist manifests (artist-owned)
- `curators.json` — listener-aid playlist curators (e.g. Hunky Brewster)
- `index.html` — zero-JS-dependency search viewer

To publish (requires YOUR GitHub auth — see `scripts/publish.sh`):

    bash scripts/publish.sh

This is FREE. It creates a public repo and enables GitHub Pages. No tier, no
cost, no account required for listeners to use the index. The protocol, not the
platform, is the product.
