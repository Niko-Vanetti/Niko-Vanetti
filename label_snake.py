#!/usr/bin/env python3
"""Envuelve el SVG de Platane/snk con etiquetas de mes y de dia.

El action escupe la rejilla pelada: colores moviendose sin nada alrededor que
permita ubicar una fecha. Aqui se le agregan los meses arriba y lun/mie/vie a
la izquierda, en los dos idiomas, ampliando el viewBox en vez de tocar el
contenido original (asi la animacion queda intacta).

Corre dentro de snake.yml y no de generate.py a proposito: la salida va a la
rama `output`, que se reescribe entera en cada corrida, asi que estos ~50 KB
por idioma no engordan el historial de main.
"""

import datetime
import re
import sys

from generate import STRINGS, esc

SRC = "dist/snake-dark.svg"
X0, Y0, STEP, COLS = 2, 2, 16, 53      # geometria observada del SVG de snk
GUTTER, HEADROOM = 34, 28              # hueco que se agrega a izquierda y arriba
INK = "#6f97b0"
FONT = "'Cascadia Code','Consolas',ui-monospace,monospace"


def grid_is_as_expected(svg):
    """snk es una dependencia externa: si algun dia cambia la rejilla, las
    etiquetas quedarian corridas y mintiendo. Mejor no ponerlas."""
    xs = sorted({float(x) for x in re.findall(r'<rect class="c" x="([-0-9.]+)"', svg)})
    return len(xs) == COLS and xs[0] == X0 and xs[1] - xs[0] == STEP


def week_starts(today):
    """Domingo de cada columna. La ultima columna es la semana en curso."""
    sunday = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
    return [sunday - datetime.timedelta(weeks=COLS - 1 - i) for i in range(COLS)]


def labels(lang, today):
    S = STRINGS[lang]
    out = []
    previous = None
    for i, start in enumerate(week_starts(today)):
        # una etiqueta por cambio de mes, salvo al final donde no cabe
        if start.month != previous and i < COLS - 2:
            out.append(f'<text x="{X0 + i * STEP}" y="{Y0 - HEADROOM - 14}" fill="{INK}" '
                       f'font-size="11" font-family="{FONT}">{esc(S["months"][start.month - 1])}</text>')
            previous = start.month
    for row, name in ((1, S["wd"][0]), (3, S["wd"][1]), (5, S["wd"][2])):
        out.append(f'<text x="{X0 - 8}" y="{Y0 + row * STEP + 9}" fill="{INK}" font-size="10" '
                   f'font-family="{FONT}" text-anchor="end">{esc(name)}</text>')
    return "".join(out)


def wrap(svg, lang, today):
    box = re.search(r'<svg viewBox="([-0-9.]+) ([-0-9.]+) ([-0-9.]+) ([-0-9.]+)"([^>]*)>', svg)
    x, y, w, h = (float(g) for g in box.groups()[:4])
    x, y, w, h = x - GUTTER, y - HEADROOM, w + GUTTER, h + HEADROOM
    head = (f'<svg viewBox="{x:g} {y:g} {w:g} {h:g}" width="{w:g}" height="{h:g}" '
            f'xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="{esc(STRINGS[lang]["h_snake"])}">')
    return head + svg[box.end():].replace("</svg>", labels(lang, today) + "</svg>")


def main():
    svg = open(SRC, encoding="utf-8").read()
    if not grid_is_as_expected(svg):
        print("snk cambio la rejilla: se deja el SVG sin etiquetar", file=sys.stderr)
        return
    today = datetime.date.today()
    for lang in STRINGS:
        path = f"dist/snake-{lang}.svg"
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(wrap(svg, lang, today))
        print("wrote", path)


if __name__ == "__main__":
    main()
