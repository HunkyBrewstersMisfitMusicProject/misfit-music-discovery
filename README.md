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
Trust-by-crypto (artist identity, no central authority):
```
python -m mmp.cli keygen --out mykey          # keep mykey.pem SECRET
python -m mmp.cli manifest --name "My Act" --key mykey.pem --payment "lnbc1..." --out manifest.json
python -m mmp.cli verify manifest.json        # anyone can verify
python -m mmp.cli index --verify-sigs         # drop unsigned/fake entries
```
`--payment` is a direct artist payment rail (Lightning/crypto). Listener pays
artist directly; we take no cut, host nothing. No listener reward token.
