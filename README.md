# Misfit Music Project — Open Discovery

An **open, non-tiered music discovery index**. Artists own their manifests;
curators help listeners find them. No account, no tier, no cost.

Live site: <https://hunkybrewstersmisfitmusicproject.github.io/misfit-music-discovery/>

The philosophy in one line: **listener-aid, not a gatekeeper.** Anyone can be
discovered here. There is no application, no approval queue, no paid tier — only
a published manifest and a place that reads it.

## How it works

The site is a single static page (`index.html`) with **no build step and no
backend**. At load time it fetches plain JSON and renders it:

- `registry.json` — an ordered list of manifest filenames (the artist index).
- `<artist>.json` — one manifest per artist (name, location, genres, bio,
  contact, links, optional preview clip).
- `curators.json` — playlist curators who help listeners navigate the catalog.

Adding an artist is a **pure data operation**: drop a `<name>.json`, append its
filename to `registry.json`. No code changes, no deploy config.

## Manifest format

Each artist manifest is plain JSON. Example:

```json
{
  "manifest_version": "0.1.0",
  "generated_at": "2026-08-02T00:00:00+00:00",
  "name": "Midnight Circuit",
  "location": "Tokyo, Japan",
  "genres": ["synthwave", "ambient", "electronic"],
  "bio": "Quiet, deep synthwave with smooth sine textures and subtle movement.",
  "links": [
    { "kind": "bandcamp", "url": "https://midnightcircuit.bandcamp.com/" },
    { "kind": "soundcloud", "url": "https://soundcloud.com/midnightcircuit" }
  ],
  "contact": "mid@midnightcircuit.jp",
  "preview": "previews/midnight-circuit.wav"
}
```

Field notes:

- `manifest_version`, `generated_at` — provenance. Bump the version when you
  change the schema.
- `bio`, `contact`, `links` — surfaced on the page. `contact` is optional.
- `preview` — a path (e.g. `previews/<name>.wav`) to a short audio clip. If the
  file is absent, the page shows **"preview pending"** rather than a broken
  player. Add the file to enable playback — no code change.

**You own your manifest.** Host it anywhere — your own site, GitHub Pages, IPFS.
This repo is one convenient index that reads it; the manifest is yours.

## Optional: audio previews

1. Place a clip at `previews/<name>.wav` (or `.mp3`).
2. Set `"preview": "previews/<name>.wav"` in the manifest.

The player appears automatically.

## SEO / discoverability

The site ships with:

- `<meta name="description">`, Open Graph + Twitter Card tags, and a canonical
  URL in `index.html`.
- `og-image.svg` — a 1200×630 social card.
- `robots.txt` and `sitemap.xml` for crawlers.
- JSON-LD `MusicGroup` / `Person` structured data, generated from the live
  manifests so it never drifts from the catalog.

## Local preview

```bash
git clone https://github.com/HunkyBrewstersMisfitMusicProject/misfit-music-discovery.git
cd misfit-music-discovery
python3 -m http.server 8099
# open http://127.0.0.1:8099/
```

A static file server is required (the page `fetch`es the JSON over HTTP, which
`file://` blocks).

## Manifest schema & validation

Manifests follow `manifest.schema.json` (JSON Schema 2020-12). A validator checks
every manifest for consistency:

```bash
python3 validate_manifests.py
```

The validator uses the `jsonschema` package when available. If it isn't
installed, it falls back to a built-in structural check (required fields, non-empty
`genres`/`links`, `preview` must be a string or `null`). For full schema
enforcement, install it first:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install jsonschema
python3 validate_manifests.py
```

The canonical manifest fields are:

| Field               | Type            | Notes                                         |
|---------------------|-----------------|-----------------------------------------------|
| `manifest_version`  | string (semver) | Bump on schema changes.                       |
| `generated_at`      | date-time       | Last update timestamp.                        |
| `name`              | string          | Artist/project name.                          |
| `location`          | string          | Human-readable location.                      |
| `genres`            | string[]        | Non-empty; used for search.                   |
| `bio`               | string          | Plain text.                                   |
| `contact`           | string \| null  | Optional contact email.                       |
| `links`             | object[]        | `{ kind, url }`; `kind` from a known set.     |
| `preview`           | string \| null  | Path to a clip, or `null` ("preview pending").|
| `releases`          | object[]        | Optional; omit entirely when empty.           |

`owner_note` (an earlier duplicated boilerplate) was removed during
consolidation — the ownership statement now lives in this README.

## Contributing

- **Artists:** publish a manifest and ask to be listed, or self-host and share
  the URL.
- **Curators:** add a playlist entry to `curators.json`.

No gatekeeping. Listener-aid only.

## License

Manifests are owned by their artists. The site code is open for reuse under the
terms of this repository.
