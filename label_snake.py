#!/usr/bin/env python3
"""Envuelve el SVG de Platane/snk con etiquetas de mes y de dia.

El action escupe la rejilla pelada: colores moviendose sin nada alrededor que
permita ubicar una fecha. Aqui se le agregan los meses arriba y lun/mie/vie a
la izquierda, en los dos idiomas, ampliando el viewBox en vez de tocar el
contenido original (asi la animacion queda intacta).

Corre dentro de snake.yml y no de generate.py a proposito: la salida va a la
rama `output`, que se reescribe entera en cada corrida, asi que estos ~50 KB
por idioma no engordan el historial de main.

La geometria se deduce del propio SVG. Antes estaba fijada a mano y la
comprobacion buscaba `class="c"` exacto, que solo matchea las celdas vacias:
en cuanto una columna entera tuvo actividad conto 52 en vez de 53, la guarda
salto y dejo de generar snake-{lang}.svg. El README apuntaba ahi y quedo con
una imagen rota. De ahi las dos lecciones que rigen este archivo: deducir en
vez de suponer, y escribir SIEMPRE los dos archivos.
"""

import datetime
import re
import shutil
import sys

from generate import STRINGS, esc

SRC = "dist/snake-dark.svg"
GUTTER, HEADROOM = 34, 28              # hueco que se agrega a izquierda y arriba
INK = "#6f97b0"
FONT = "'Cascadia Code','Consolas',ui-monospace,monospace"
CELL = re.compile(r'<rect class="c[^"]*" x="([-0-9.]+)" y="([-0-9.]+)"')


def geometry(svg):
    """Rejilla deducida del SVG: origen, paso y numero de columnas.

    Devuelve None si no se reconoce, y entonces no se etiqueta: mejor sin
    etiquetas que con etiquetas corridas mintiendo sobre las fechas."""
    cells = CELL.findall(svg)
    xs = sorted({float(x) for x, _ in cells})
    ys = sorted({float(y) for _, y in cells})
    if len(xs) < 50 or len(ys) != 7:
        return None
    steps = {round(b - a, 3) for a, b in zip(xs, xs[1:])}
    if len(steps) != 1:                # columnas irregulares: no se reconoce
        return None
    return {"x0": xs[0], "y0": ys[0], "step": steps.pop(), "cols": len(xs)}


def week_starts(today, cols):
    """Domingo de cada columna. La ultima columna es la semana en curso."""
    sunday = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
    return [sunday - datetime.timedelta(weeks=cols - 1 - i) for i in range(cols)]


def labels(lang, today, g):
    S = STRINGS[lang]
    out = []
    previous = None
    for i, start in enumerate(week_starts(today, g["cols"])):
        # una etiqueta por cambio de mes, salvo al final donde no cabe
        if start.month != previous and i < g["cols"] - 2:
            out.append(f'<text x="{g["x0"] + i * g["step"]:g}" '
                       f'y="{g["y0"] - HEADROOM - 14:g}" fill="{INK}" font-size="11" '
                       f'font-family="{FONT}">{esc(S["months"][start.month - 1])}</text>')
            previous = start.month
    for row, name in ((1, S["wd"][0]), (3, S["wd"][1]), (5, S["wd"][2])):
        out.append(f'<text x="{g["x0"] - 8:g}" y="{g["y0"] + row * g["step"] + 9:g}" '
                   f'fill="{INK}" font-size="10" font-family="{FONT}" '
                   f'text-anchor="end">{esc(name)}</text>')
    return "".join(out)


def wrap(svg, lang, today, g):
    box = re.search(r'<svg viewBox="([-0-9.]+) ([-0-9.]+) ([-0-9.]+) ([-0-9.]+)"[^>]*>', svg)
    x, y, w, h = (float(v) for v in box.groups())
    x, y, w, h = x - GUTTER, y - HEADROOM, w + GUTTER, h + HEADROOM
    head = (f'<svg viewBox="{x:g} {y:g} {w:g} {h:g}" width="{w:g}" height="{h:g}" '
            f'xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="{esc(STRINGS[lang]["h_snake"])}">')
    return head + svg[box.end():].replace("</svg>", labels(lang, today, g) + "</svg>")


def main():
    svg = open(SRC, encoding="utf-8").read()
    g = geometry(svg)
    today = datetime.date.today()
    if g is None:
        print("rejilla no reconocida: se copia sin etiquetar", file=sys.stderr)
    for lang in STRINGS:
        path = f"dist/snake-{lang}.svg"
        # Pase lo que pase, el archivo que el README referencia debe existir.
        if g is None:
            shutil.copyfile(SRC, path)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(wrap(svg, lang, today, g))
        print("wrote", path)


if __name__ == "__main__":
    main()
