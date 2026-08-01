# Misfit Music Project — Open Discovery Index

Free, open, non-tiered discovery for independent artists. Artists own their
manifests; listeners browse with no account and no tracking.

Live: https://hunkybrewstersmisfitmusicproject.github.io/misfit-music-discovery/

Add an artist (local):
```
python -m mmp.cli manifest --name "My Act" --link https://myact.bandcamp.com
```
Publish (needs `gh` auth):
```
python scripts/build_site.py && bash scripts/publish.sh
```
