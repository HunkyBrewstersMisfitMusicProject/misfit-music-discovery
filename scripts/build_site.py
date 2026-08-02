#!/usr/bin/env python3
"""Build the GitHub-Pages site from seed data.

Produces gh-pages/ with:
  - registry.json   (list of manifest URLs, relative)
  - curators.json   (curator records)
  - <artist>.json   (mirrored manifests, relative-linked)
  - index.html      (zero-dependency viewer: search artists + curators)

All URLs are RELATIVE so the same tree works on GitHub Pages, IPFS, or any
static host. No account, no tier, no cost. The protocol is the product.

Run: python scripts/build_site.py
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seed")
OUT = os.path.join(ROOT, "gh-pages")


def main():
    os.makedirs(OUT, exist_ok=True)
    # clean previous build (but keep .git / CNAME / previews if present)
    for name in os.listdir(OUT):
        if name in (".git", "CNAME", "README.md", "previews"):
            continue
        p = os.path.join(OUT, name)
        if os.path.isfile(p):
            os.remove(p)
        else:
            shutil.rmtree(p)

    # Copy seed manifests into gh-pages as the hosted manifests
    manifests = {}
    for fn in os.listdir(SEED):
        if fn.endswith(".json") and fn != "curators.json":
            src = os.path.join(SEED, fn)
            with open(src, encoding="utf-8") as fh:
                obj = json.load(fh)
            dst = os.path.join(OUT, fn)
            with open(dst, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            manifests[fn] = obj

    # Copy preview clips (if any) into gh-pages
    previews_src = os.path.join(ROOT, "gh-pages", "previews")
    previews_dst = os.path.join(OUT, "previews")
    if os.path.isdir(previews_src):
        os.makedirs(previews_dst, exist_ok=True)
        for fn in os.listdir(previews_src):
            shutil.copy2(os.path.join(previews_src, fn),
                         os.path.join(previews_dst, fn))

    # Build registry (relative URLs to the mirrored manifests)
    registry = [fn for fn in manifests]
    with open(os.path.join(OUT, "registry.json"), "w", encoding="utf-8") as fh:
        json.dump(registry, fh, indent=2)
        fh.write("\n")

    # Copy curators
    curators_src = os.path.join(SEED, "curators.json")
    with open(curators_src, encoding="utf-8") as fh:
        curators = json.load(fh)
    with open(os.path.join(OUT, "curators.json"), "w", encoding="utf-8") as fh:
        json.dump(curators, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # Static viewer
    html = _viewer_html(manifests, curators)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)

    print(f"Built gh-pages/ with {len(manifests)} manifests, "
          f"{len(curators)} curators, "
          f"{sum(1 for m in manifests.values() if m.get('preview'))} with previews.")


def _viewer_html(manifests, curators):
    artists = [{"name": m.get("name"), "location": m.get("location"),
                "genres": m.get("genres", []), "links": m.get("links", []),
                "preview": bool(m.get("preview"))}
               for m in manifests.values()]
    payload = {"artists": artists, "curators": curators}
    data = json.dumps(payload, ensure_ascii=False)
    return _HTML_TEMPLATE.replace("/*__DATA__*/", data)


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Misfit Music Project — Open Discovery</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 760px; margin: 2rem auto;
         padding: 0 1rem; color: #111; line-height: 1.5; }
  h1 { font-size: 1.4rem; }
  .tag { display: inline-block; background: #eee; border-radius: 4px;
         padding: 1px 6px; font-size: .8rem; margin: 2px; }
  input { width: 100%; padding: .5rem; font-size: 1rem; margin-bottom: 1rem; }
  .card { border: 1px solid #ddd; border-radius: 8px; padding: .75rem 1rem;
          margin-bottom: .75rem; }
  a { color: #0a6; }
  .curator { background: #faf6ff; }
  .note { font-size: .85rem; color: #666; }
</style>
</head>
<body>
<h1>Misfit Music Project — Open Discovery</h1>
<p class="note">An open, non-tiered discovery index. Artists own their manifests;
curators help listeners find them. No account, no tier, no cost.
<a href="registry.json">registry.json</a></p>
<input id="q" placeholder="Search by name, genre, city, or curator…" autofocus>
<div id="out"></div>
<script>
const DATA = /*__DATA__*/;
const all = [
  ...DATA.artists.map(a => ({type:"artist", ...a})),
  ...DATA.curators.map(c => ({type:"curator", name:c.name, blurb:c.blurb,
       links:(c.playlists||[]).map(p=>({kind:"playlist", url:p.url}))}))
];
function render(q){
  q = (q||"").toLowerCase();
  const out = document.getElementById("out");
  out.innerHTML = "";
  for(const x of all){
    const hay = [x.name, x.location, (x.genres||[]).join(" "), x.blurb||""]
      .join(" ").toLowerCase();
    if(q && !hay.includes(q)) continue;
    const div = document.createElement("div");
    div.className = "card" + (x.type==="curator" ? " curator" : "");
    let html = `<strong>${x.name}</strong>`;
    if(x.preview){ html += ` <span class="tag" style="background:#cfe;">preview clip</span>`; }
    if(x.type==="curator"){ html += ` <span class="tag">playlist curator</span>`; }
    if(x.location){ html += ` <span class="tag">${x.location}</span>`; }
    for(const g of (x.genres||[])){ html += ` <span class="tag">${g}</span>`; }
    if(x.blurb){ html += `<div class="note">${x.blurb}</div>`; }
    for(const l of (x.links||[])){
      html += `<div><a href="${l.url}" target="_blank" rel="noopener">${l.url}</a></div>`;
    }
    div.innerHTML = html;
    out.appendChild(div);
  }
}
document.getElementById("q").addEventListener("input", e=>render(e.target.value));
render("");
</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
