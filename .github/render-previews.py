"""Render the bare Arkenswoop PCB and its backplate from the repository root."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pcbnew
from lxml import etree


def export_png(svg, area, width, output):
    # PcbDraw's SVG coordinates are millimetres. Frame the routed outline so
    # oversized, clipped silkscreen artwork cannot shift the backplate preview.
    x, y, w, h = area
    svg.set("viewBox", f"{x} {y} {w} {h}")
    svg.set("width", f"{w}mm")
    svg.set("height", f"{h}mm")
    dest = Path("images/exports") / output
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["rsvg-convert", "--width", str(width), "--output", str(dest)],
        input=etree.tostring(svg), check=True,
    )


def render(board_path, outputs, display_detail=False):
    board_path = board_path.resolve(strict=True)
    board = pcbnew.LoadBoard(str(board_path))
    bounds = board.GetBoardEdgesBoundingBox()
    margin = 3
    top = pcbnew.ToMM(bounds.GetTop()) - margin
    width = pcbnew.ToMM(bounds.GetWidth()) + 2 * margin
    height = pcbnew.ToMM(bounds.GetHeight()) + 2 * margin

    with TemporaryDirectory() as tmp:
        for side, output in outputs.items():
            path = Path(tmp) / f"{side}.svg"
            subprocess.run([
                "pcbdraw", "plot", "--style", "set-black-enig", "--no-components",
                "--drill-holes", "--side", side, str(board_path), str(path),
            ], check=True)
            svg = etree.parse(str(path)).getroot()
            left = bounds.GetLeft() if side == "front" else -bounds.GetRight()
            area = (pcbnew.ToMM(left) - margin, top, width, height)
            export_png(svg, area, 2200, output)
            if display_detail and side == "front":
                # Include the CS marking, display jumpers and adjacent battery pads.
                display = board.FindFootprintByReference("O1").GetPosition()
                detail = (pcbnew.ToMM(display.x) - 10, pcbnew.ToMM(display.y) - 7, 24, 12)
                export_png(svg, detail, 960, "arkenswoop/display.png")


boards = Path("pcbs/3x5_2")
render(boards / "arkenswoop/arkenswoop.kicad_pcb",
       {"front": "arkenswoop/front.png", "back": "arkenswoop/back.png"}, display_detail=True)
render(boards / "plates/plates.kicad_pcb",
       {"front": "plates/left.png", "back": "plates/right.png"})
