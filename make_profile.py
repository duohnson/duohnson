#!/usr/bin/env python3
"""Genera dark_mode.svg (estilo neofetch/terminal) a partir de:
   - ascii_art.txt  (arte braille de tu cara; regenerable con gen_ascii.py)
   - CONFIG de abajo (edita libremente los campos)
Corre:  python3 make_profile.py
"""

# ============================ EDITA AQUÍ ============================
NAME   = "duohnson"          # originalmente se hizo fork a: TVTvirus@github, sus respectivos creditos..
HANDLE = "github"

# Cada fila: ("field", clave, valor)  |  ("blank",)
# Quita/añade filas a gusto. NO hay campo de edad a propósito.
# Los {placeholders} se rellenan desde data.json (lo actualiza update_data.py).
ROWS = [
    ("field", "OS",      "Ubuntu 24.04.5 LTS  ·  Linux Servers"),
    ("field", "Host",    "Self-hosted homelab"),
    ("field", "Role",    "Backend & SysAdmin"),
    ("field", "IDE",     "zed ide · notepad++"),
    ("blank",),
    ("field", "Languages.Programming", "Python, TypeScript, Java"),
    ("field", "Languages.Real",        "Español, English"),
    ("blank",),
    ("field", "Hobbies.Software", "Scripting, automation, and backgr processes"),
    ("field", "Hobbies.Music",    "Alternative Rock · Nu Metal · Hard Rock"),
    ("blank",),
    ("field", "Last Played", "{last_played}"),
    ("blank",),
    ("field", "Contact.Discord", "duohnson"),
    ("field", "Contact.Email",   "duohnson@gmail.com"),
    ("blank",),
    ("field", "Stats.Repos",   "{repos}  ·  [y]{stars} stars[/]  ·  {followers} followers"),
    ("field", "Stats.Commits", "{commits}"),
    ("field", "Stats.Lines of Code", "{loc_net} ([g]{loc_add}++[/], [r]{loc_del}--[/])"),
    ("field", "Stats.Status", "{stats_status}"),
]

# Paletas: se genera un SVG por tema (GitHub elige con prefers-color-scheme)
THEMES = {
    "dark_mode.svg": dict(
        BG="#0d1117", BORDER="#30363d",
        C_ART="#b9c0cc",    # la cara
        C_NAME="#7ee787",   # tu nombre
        C_AT="#8b949e",     # @github y la regla
        C_KEY="#58a6ff",    # las claves (OS:, IDE:, ...)
        C_VAL="#c9d1d9",    # los valores
        C_CURSOR="#7ee787",
        C_ADD="#3fb950",    # [g] verde (lineas anadidas)
        C_DEL="#f85149",    # [r] rojo (lineas borradas)
        C_STAR="#e3b341",   # [y] dorado (stars)
    ),
    "light_mode.svg": dict(
        BG="#ffffff", BORDER="#d0d7de",
        C_ART="#3f4750",
        C_NAME="#1a7f37",
        C_AT="#59636e",
        C_KEY="#0969da",
        C_VAL="#1f2328",
        C_CURSOR="#1a7f37",
        C_ADD="#1a7f37",
        C_DEL="#cf222e",
        C_STAR="#9a6700",
    ),
}
# ===================================================================

FS_ART = 12.5
LH_ART = FS_ART * 1.2          # braille conserva el aspecto con lh = 2*avance (~1.2em)
CH_ART = FS_ART * 0.602        # avance monoespaciado tipico
FS_TXT, LH_TXT = 13.5, 22.0
PAD = 24


import json
import re

class _Safe(dict):
    def __missing__(self, k):
        return "?"

try:
    with open("data.json") as _f:
        DATA = _Safe(json.load(_f))
except FileNotFoundError:
    DATA = _Safe()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    art = open("ascii_art.txt").read().split("\n")
    art_w = max(len(l) for l in art)
    col2_x = PAD + art_w * CH_ART + 40
    width = int(col2_x + 510)
    height = int(max(len(art) * LH_ART, len(ROWS) * LH_TXT) + PAD * 2 + 16)

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Consolas, \'DejaVu Sans Mono\', '
        f'\'Adwaita Mono\', \'Courier New\', monospace">'
    )
    # Animaciones con fill-mode backwards: por defecto TODO es visible (opacity 1),
    # asi el SVG se ve entero en visores sin CSS; en navegador la animacion
    # aplica el estado from{opacity:0} durante el delay y hace el tipeo.
    out.append(
        "<style>"
        "@keyframes fade{from{opacity:0}to{opacity:1}}"
        "@keyframes blink{50%{opacity:0}}"
        ".art tspan{animation:fade .01s ease backwards}"
        ".row{animation:fade .12s ease backwards}"
        "</style>"
    )
    # marco
    out.append(
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>'
    )

    # ---- arte braille (columna izquierda) ----
    out.append(f'<text class="art" x="{PAD}" y="{PAD+FS_ART}" xml:space="preserve" '
               f'font-size="{FS_ART}" fill="{C_ART}">')
    for i, line in enumerate(art):
        dy = 0 if i == 0 else LH_ART
        out.append(f'<tspan x="{PAD}" dy="{dy}" style="animation-delay:{0.02*i:.2f}s">{esc(line)}</tspan>')
    out.append("</text>")

    # ---- campos (columna derecha) ----
    y = PAD + FS_TXT
    art_done = 0.02 * len(art)
    line_idx = 0

    def row_text(inner, delay):
        return (f'<text class="row" x="{col2_x}" y="{y}" font-size="{FS_TXT}" '
                f'xml:space="preserve" style="animation-delay:{delay:.2f}s">{inner}</text>')

    # titulo:  NAME@github  +  regla
    inner = (f'<tspan fill="{C_NAME}" font-weight="bold">{esc(NAME)}</tspan>'
             f'<tspan fill="{C_AT}">@{esc(HANDLE)}</tspan>')
    out.append(row_text(inner, art_done + 0.10)); y += LH_TXT; line_idx += 1
    rule = "-" * (len(NAME) + 1 + len(HANDLE))
    out.append(row_text(f'<tspan fill="{C_AT}">{rule}</tspan>', art_done + 0.22)); y += LH_TXT; line_idx += 1

    for row in ROWS:
        d = art_done + 0.10 + 0.12 * line_idx
        if row[0] == "blank":
            y += LH_TXT * 0.5; line_idx += 1; continue
        _, key, val = row
        val = val.format_map(DATA)
        # markup inline [g]...[/] verde, [r]...[/] rojo, [y]...[/] dorado
        inline = {"g": C_ADD, "r": C_DEL, "y": C_STAR}
        val_spans = []
        for m in re.finditer(r'\[([gry])\](.*?)\[/\]|([^\[]+|\[)', val):
            tag, txt, plain = m.groups()
            if tag:
                val_spans.append(f'<tspan fill="{inline[tag]}">{esc(txt)}</tspan>')
            else:
                val_spans.append(f'<tspan fill="{C_VAL}">{esc(plain)}</tspan>')
        inner = (f'<tspan fill="{C_KEY}" font-weight="bold">{esc(key)}</tspan>'
                 f'<tspan fill="{C_AT}">: </tspan>' + "".join(val_spans))
        out.append(row_text(inner, d)); y += LH_TXT; line_idx += 1

    # cursor: aparece al final y parpadea (visible fijo en visores sin CSS)
    d = art_done + 0.10 + 0.12 * line_idx
    out.append(f'<text x="{col2_x}" y="{y}" font-size="{FS_TXT}" fill="{C_CURSOR}" '
               f'style="animation:fade .01s backwards {d:.2f}s, blink 1.1s steps(1) {d+.3:.2f}s infinite">'
               f'&#9611;</text>')

    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    for fname, theme in THEMES.items():
        globals().update(theme)      # build() lee los colores como globales
        svg = build()
        with open(fname, "w") as f:
            f.write(svg)
        print(f"Escrito {fname} ({len(svg)} bytes)")
