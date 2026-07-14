#!/usr/bin/env python3
"""Generate the Buddy portfolio website into site/ from the repo's documents.

Sources: docs/portfolio/milestones/*.md, docs/analysis/*.md (generated exports),
docs/portfolio/log/*.md, docs/decisions/ADR-*.md, assets/figures/*.svg.
Landing-page spec chips are computed live from buddy_calcs — the site is a
parametric artifact like the figures.

    python3 tools/site/build_site.py     (also runs at the end of tools/build.py)

Output is committed. View: python3 -m http.server -d site 8080
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from buddy_calcs import P, R  # noqa: E402
from buddy_calcs import power  # noqa: E402
from buddy_calcs.drive import summary as drive_summary  # noqa: E402

SITE = ROOT / "site"
CFG = yaml.safe_load((ROOT / "tools" / "site" / "site_config.yaml").read_text())
IDENTITY = " · ".join(
    [f'<b>{CFG["name"]}</b>', CFG["role"]] +
    [f'<a href="{u}">{k}</a>' for k, u in (CFG.get("links") or {}).items()])
KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist"

CSS = """
:root{
  --page:#f7f7f4; --surface:#fcfcfb; --ink:#0b0b0b; --muted:#52514e;
  --faint:#898781; --rule:#e1e0d9; --accent:#2a78d6; --accent-deep:#1c5cab;
  --sans:'Helvetica Neue',Helvetica,Arial,system-ui,sans-serif;
  --mono:'SF Mono',Menlo,Consolas,'Liberation Mono',monospace;
}
*{box-sizing:border-box;margin:0}
html{-webkit-text-size-adjust:100%}
body{background:var(--page);color:var(--ink);font:16px/1.65 var(--sans);}
a{color:var(--accent-deep);text-decoration:none;border-bottom:1px solid var(--rule)}
a:hover{color:var(--accent);border-bottom-color:var(--accent)}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wrap{max-width:76rem;margin:0 auto;padding:0 1.5rem}
header.top{border-bottom:1px solid var(--rule);background:var(--surface)}
header.top .wrap{display:flex;align-items:baseline;gap:1.5rem;padding-top:.9rem;padding-bottom:.9rem;flex-wrap:wrap}
.brand{font-weight:700;font-size:1.05rem;letter-spacing:-.01em;border:none;color:var(--ink)}
nav{display:flex;gap:1.1rem;font-family:var(--mono);font-size:.78rem}
nav a{border:none;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
nav a:hover,nav a.here{color:var(--accent-deep)}
.eyebrow{font-family:var(--mono);font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;color:var(--faint)}
main{padding:2.8rem 0 4rem}
h1{font-size:2rem;line-height:1.15;letter-spacing:-.02em;text-wrap:balance;margin:.35rem 0 .6rem}
.lede{color:var(--muted);max-width:46rem;font-size:1.06rem}
.meta{font-family:var(--mono);font-size:.75rem;color:var(--faint);margin-top:.5rem}
.chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:1.6rem 0 0}
.chip{background:var(--surface);border:1px solid var(--rule);padding:.42rem .7rem;font-family:var(--mono);font-size:.78rem;color:var(--muted)}
.chip b{color:var(--ink);font-weight:600}
section.block{margin-top:3.2rem}
.sec-head{display:flex;baseline;justify-content:space-between;border-bottom:1px solid var(--rule);padding-bottom:.5rem;margin-bottom:1.2rem}
.sec-head h2{font-size:1.15rem;letter-spacing:-.01em}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(19rem,1fr));gap:1rem}
.card{background:var(--surface);border:1px solid var(--rule);padding:1.1rem 1.2rem;display:flex;flex-direction:column;gap:.45rem}
.card h3{font-size:1rem;line-height:1.3}
.card h3 a{border:none;color:var(--ink)}
.card h3 a:hover{color:var(--accent-deep)}
.card p{font-size:.88rem;color:var(--muted)}
.card .meta{margin-top:auto}
.decisions li,.loglist li{padding:.55rem 0;border-bottom:1px solid var(--rule);display:flex;gap:1rem;align-items:baseline;flex-wrap:wrap}
.decisions .id{font-family:var(--mono);font-size:.75rem;color:var(--faint);min-width:5.2rem}
.status{font-family:var(--mono);font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;padding:.1rem .45rem;border:1px solid var(--rule);color:var(--muted);margin-left:auto}
article{max-width:47rem}
article h1{font-size:1.75rem}
article h2{font-size:1.25rem;letter-spacing:-.01em;margin:2.4rem 0 .8rem;padding-top:1.2rem;border-top:1px solid var(--rule)}
article h3{font-size:1.02rem;margin:1.6rem 0 .5rem}
article p{margin:.85rem 0}
article ul,article ol{margin:.85rem 0;padding-left:1.4rem}
article li{margin:.35rem 0}
article li::marker{color:var(--faint)}
article blockquote{border-left:3px solid var(--rule);padding:.2rem 0 .2rem 1rem;color:var(--muted);margin:1rem 0}
article img{max-width:100%;background:var(--surface);border:1px solid var(--rule);padding:.6rem;margin:1.4rem 0 .4rem}
article img+em, article em:has(+img){display:block}
article table{border-collapse:collapse;width:100%;font-size:.88rem;margin:1rem 0}
article th{text-align:left;font-family:var(--mono);font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--faint);font-weight:500}
article th,article td{padding:.5rem .7rem .5rem 0;border-bottom:1px solid var(--rule);vertical-align:top}
article td{font-variant-numeric:tabular-nums}
.tablewrap{overflow-x:auto}
article code{font-family:var(--mono);font-size:.85em;background:var(--surface);border:1px solid var(--rule);padding:.05em .3em}
article pre{background:var(--surface);border:1px solid var(--rule);padding:.9rem 1rem;overflow-x:auto;margin:1rem 0}
article pre code{border:none;padding:0;background:none;font-size:.8rem;line-height:1.55}
article hr{border:none;border-top:1px solid var(--rule);margin:2rem 0}
.katex-display{overflow-x:auto;padding:.2rem 0}
footer{border-top:1px solid var(--rule);color:var(--faint);font-family:var(--mono);font-size:.72rem}
footer .wrap{padding-top:1rem;padding-bottom:2.2rem}
footer .who{font-family:var(--sans);font-size:.85rem;color:var(--muted);margin-bottom:.4rem}
footer .who b{color:var(--ink)}
footer a{border:none}
@media (prefers-reduced-motion:no-preference){a{transition:color .12s ease}}
"""

MATH_TOKEN = "XMATHSPAN{}XEND"


def protect_math(text: str) -> tuple[str, list[str]]:
    spans: list[str] = []

    def stash(match: re.Match) -> str:
        spans.append(match.group(0))
        return MATH_TOKEN.format(len(spans) - 1)

    text = re.sub(r"\$\$.+?\$\$", stash, text, flags=re.S)
    text = re.sub(r"(?<![\w$])\$(?!\s)([^$\n]+?)(?<!\s)\$(?![\w$])", stash, text)
    return text, spans


def render_md(text: str) -> str:
    text, spans = protect_math(text)
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "smarty"])
    for i, span in enumerate(spans):
        html = html.replace(MATH_TOKEN.format(i), span)
    html = html.replace("<table>", '<div class="tablewrap"><table>').replace(
        "</table>", "</table></div>")
    return html


def rewrite_links(html: str, page_map: dict[str, str]) -> str:
    html = re.sub(r'(?:\.\./)*assets/figures/([\w.-]+\.svg)', r'../figures/\1', html)
    for md_name, target in page_map.items():
        html = re.sub(r'href="[^"]*' + re.escape(md_name) + r'"',
                      f'href="{target}"', html)
    # repo documents that aren't site pages: show as code, not broken links
    html = re.sub(r'<a href="[^"]*\.md(?:#[^"]*)?">(.*?)</a>', r'<code>\1</code>', html)
    return html


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
        body = re.sub(r"^\s*<!--.*?-->", "", body, count=1, flags=re.S)
        return meta, body.strip()
    return {}, text


def page(title: str, body: str, here: str, depth: int = 0, math: bool = False) -> str:
    rel = "../" * depth  # noqa - IDENTITY interpolated below
    links = [("index.html", "Overview", "home"),
             ("milestones/index.html", "Milestones", "milestones"),
             ("analysis/index.html", "Analyses", "analysis"),
             ("decisions/index.html", "Decisions", "decisions"),
             ("log.html", "Log", "log")]
    nav = "".join(
        f'<a href="{rel}{href}" class="{"here" if key == here else ""}">{label}</a>'
        for href, label, key in links)
    katex = ""
    if math:
        katex = (f'<link rel="stylesheet" href="{KATEX}/katex.min.css">'
                 f'<script defer src="{KATEX}/katex.min.js"></script>'
                 f'<script defer src="{KATEX}/contrib/auto-render.min.js" '
                 'onload="renderMathInElement(document.body,{delimiters:[{left:\'$$\',right:\'$$\',display:true},{left:\'$\',right:\'$\',display:false}]})"></script>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Buddy</title><style>{CSS}</style>{katex}</head><body>
<header class="top"><div class="wrap">
<a class="brand" href="{rel}index.html">Buddy</a>
<span class="eyebrow">autonomous mobile robot — engineering record</span>
<nav>{nav}</nav></div></header>
<main><div class="wrap">{body}</div></main>
<footer><div class="wrap"><p class="who">{IDENTITY}</p>
Generated from the project repository by tools/site/build_site.py ·
figures and numbers regenerate from design_params.yaml</div></footer>
</body></html>"""


def spec_chips() -> str:
    d, pw = drive_summary(), power.summary()
    chips = [
        ("gross mass", f"{d.mass_kg:g} kg"),
        ("drive", "4× skid-steer"),
        ("wheel", f"{P['wheels']['radius_m'] * 2000:g} mm Hogback"),
        ("motor stall", f"{d.motor_stall:g} N·m"),
        ("pivot demand", f"{d.t_pivot['carpet_high']:.2f} N·m @ μ0.8"),
        ("designed peak", f"{pw.peak_designed:.0f} A"),
        ("battery", f"3S Li-ion ≥ {pw.ah_allocation:.0f} Ah"),
        ("runtime req", f"{pw.runtime_h * 60:.0f} min"),
        ("compute", "Jetson Orin Nano"),
    ]
    return '<div class="chips">' + "".join(
        f'<span class="chip">{k} <b>{v}</b></span>' for k, v in chips) + "</div>"


def collect(pattern: str, base: Path) -> list[tuple[dict, str, Path]]:
    out = []
    for f in sorted(base.glob(pattern)):
        meta, body = parse_frontmatter(f)
        out.append((meta, body, f))
    return out


def main() -> int:
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "figures").mkdir(parents=True)
    for svg in (ROOT / "assets" / "figures").glob("*.svg"):
        shutil.copy2(svg, SITE / "figures" / svg.name)

    # Static files that aren't generated (resume, favicon, ...) live in
    # tools/site/static/ so they survive the shutil.rmtree(SITE) above, and
    # get copied to the site root as-is.
    static_dir = ROOT / "tools" / "site" / "static"
    if static_dir.exists():
        for f in static_dir.iterdir():
            if f.is_file() and f.name != "README.md":
                shutil.copy2(f, SITE / f.name)

    milestones = collect("*.md", ROOT / "docs" / "portfolio" / "milestones")
    analyses = collect("*.md", ROOT / "docs" / "analysis")
    logs = collect("*.md", ROOT / "docs" / "portfolio" / "log")
    adrs = [f for f in sorted((ROOT / "docs" / "decisions").glob("ADR-*.md"))
            if "template" not in f.name]

    page_map: dict[str, str] = {}
    for _, _, f in milestones:
        page_map[f.name] = f"../milestones/{f.stem}.html"
    for _, _, f in analyses:
        page_map[f.name] = f"../analysis/{f.stem}.html"
    for f in adrs:
        page_map[f.name] = f"../decisions/{f.stem}.html"

    def write_article(meta: dict, body: str, src: Path, section: str) -> None:
        html = rewrite_links(render_md(body), page_map)
        date = meta.get("date", "")
        tags = ", ".join(meta.get("tags", [])) if isinstance(meta.get("tags"), list) else meta.get("tags", "")
        head = f'<p class="meta">{date}{" · " + str(tags).strip("[]") if tags else ""}</p>' if date else ""
        out = SITE / section / f"{src.stem}.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(page(meta.get("title", src.stem),
                            f"<article>{head}{html}</article>", section,
                            depth=1, math=True))

    for meta, body, f in milestones:
        write_article(meta, body, f, "milestones")
    for meta, body, f in analyses:
        write_article(meta, body, f, "analysis")

    adr_rows = []
    for f in adrs:
        text = f.read_text()
        title = re.search(r"^# (.+)$", text, re.M).group(1)
        status = (re.search(r"- Status: (.+)", text) or ["", "—"])[1]
        date = (re.search(r"- Date: (.+)", text) or ["", ""])[1]
        html = rewrite_links(render_md(text), page_map)
        (SITE / "decisions").mkdir(exist_ok=True)
        (SITE / "decisions" / f"{f.stem}.html").write_text(
            page(title, f"<article>{html}</article>", "decisions", depth=1, math=True))
        num = f.stem.split("-")[1]
        adr_rows.append(
            f'<li><span class="id">ADR-{num}</span>'
            f'<a href="decisions/{f.stem}.html">{title.split(": ", 1)[-1]}</a>'
            f'<span class="meta">{date}</span><span class="status">{status}</span></li>')

    log_html = ""
    for meta, body, f in sorted(logs, key=lambda x: str(x[2]), reverse=True):
        log_html += rewrite_links(render_md(body), {k: v.replace("../", "") for k, v in page_map.items()})
    (SITE / "log.html").write_text(
        page("Engineering Log", f"<article>{log_html}</article>", "log", math=True))

    def cards(items: list, section: str, prefix: str = "") -> str:
        cs = ""
        for meta, _, f in sorted(items, key=lambda x: x[0].get("date", ""), reverse=True):
            figs = meta.get("figures", "")
            cs += (f'<div class="card"><span class="eyebrow">{meta.get("type", section)}</span>'
                   f'<h3><a href="{prefix}{section}/{f.stem}.html">{meta.get("title", f.stem)}</a></h3>'
                   f'<p>{meta.get("summary", "")}</p>'
                   f'<span class="meta">{meta.get("date", "")}</span></div>')
        return f'<div class="cards">{cs}</div>'

    for section, items, blurb in [
        ("milestones", milestones, "One illustrated report per completed phase."),
        ("analysis", analyses, "Checkable derivations: equations, substitutions, limits of validity."),
    ]:
        body = (f'<span class="eyebrow">{section}</span><h1>{blurb}</h1>'
                + cards(items, section, prefix="../").replace(f'href="../{section}/', 'href="'))
        (SITE / section / "index.html").write_text(
            page(section.capitalize(), body, section, depth=1))
    dec_rows_local = "".join(r.replace('href="decisions/', 'href="') for r in adr_rows)
    (SITE / "decisions" / "index.html").write_text(
        page("Decisions", '<span class="eyebrow">decision record</span>'
             '<h1>Architecture Decision Records</h1>'
             f'<ul class="decisions" style="list-style:none;padding:0">{dec_rows_local}</ul>',
             "decisions", depth=1))

    index_body = f"""
<span class="eyebrow">project record · v0.1 design phase</span>
<h1>Buddy — an indoor autonomous robot, designed out loud</h1>
<p class="lede">A ~20 kg four-wheel skid-steer base (ROS 2, Jetson Orin Nano) built as a
complete engineering record: every component is sized from first-principles derivations
that can be checked by hand, every figure regenerates from one parameter file, and every
decision is written down with the conditions that would reverse it.</p>
{spec_chips()}
<p class="meta" style="margin-top:1rem">{IDENTITY}</p>
<section class="block"><div class="sec-head"><h2>Milestones</h2>
<span class="eyebrow">one illustrated report per phase</span></div>{cards(milestones, "milestones")}</section>
<section class="block"><div class="sec-head"><h2>Analyses</h2>
<span class="eyebrow">checkable derivations — equations, substitutions, limits of validity</span></div>{cards(analyses, "analysis")}</section>
<section class="block"><div class="sec-head"><h2>Decision record</h2>
<span class="eyebrow">architecture decision records</span></div>
<ul class="decisions" style="list-style:none;padding:0">{"".join(adr_rows)}</ul></section>
<section class="block"><div class="sec-head"><h2>Engineering log</h2>
<span class="eyebrow">dated, same-day, failures included</span></div>
<p class="lede" style="font-size:.95rem">The raw record behind the milestones —
<a href="log.html">read the full log</a>.</p></section>
"""
    (SITE / "index.html").write_text(page("Overview", index_body, "home"))
    print(f"site built: {sum(1 for _ in SITE.rglob('*.html'))} pages -> {SITE.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
