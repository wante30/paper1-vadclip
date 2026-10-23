#!/usr/bin/env python3
"""Apply the final, local technical corrections to the existing Figure 1.

The original overview.png is embedded unchanged. Small vector masks, labels,
formulae, and one rerouted edge are placed on top; no panel is regenerated.
Run from any directory with Python, PyMuPDF, Pillow and Matplotlib installed.
The corrected PDF retains the original aspect ratio and is ready for LaTeX.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

import fitz
import matplotlib as mpl
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
BLUE = (0.0, 0.43, 1.0)
INK = (0.03, 0.03, 0.04)
PALE_BLUE = tuple(v / 255 for v in (233, 245, 252))
PALE_WHITE = tuple(v / 255 for v in (250, 250, 251))
SOURCE_SIZE = (1816, 735)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path,
                        default=ROOT / 'paper/figures/overview.png')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'paper/figures/overview_corrected.pdf')
    parser.add_argument('--preview', type=Path, default=ROOT /
                        'ccfa-workfiles/final-revision/build/overview_corrected_preview.png')
    parser.add_argument('--font-dir', type=Path, default=Path('C:/Windows/Fonts'))
    args = parser.parse_args()

    with Image.open(args.source) as source_image:
        if source_image.size != SOURCE_SIZE:
            raise ValueError(f'Expected {SOURCE_SIZE}, got {source_image.size}. '
                             'Patch coordinates are specific to this Figure 1.')
    before_hash = sha256(args.source)
    for path in (args.output, args.preview):
        path.parent.mkdir(parents=True, exist_ok=True)

    mpl.rcParams.update({'mathtext.fontset': 'stix', 'pdf.fonttype': 42,
                         'savefig.transparent': True})
    doc = fitz.open()
    page = doc.new_page(width=SOURCE_SIZE[0], height=SOURCE_SIZE[1])
    page.insert_image(page.rect, filename=str(args.source))
    font_names = {'regular': 'times.ttf', 'bold': 'timesbd.ttf',
                  'italic': 'timesi.ttf'}
    fonts = {}
    for role, filename in font_names.items():
        path = args.font_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f'Times New Roman is required: {path}')
        fonts[role] = fitz.Font(fontfile=str(path))
        page.insert_font(fontname=f'patch_{role}', fontfile=str(path))

    mask_regions = []

    def cover(box, color=PALE_BLUE):
        page.draw_rect(fitz.Rect(box), color=None, fill=color, overlay=True)
        mask_regions.append(list(box))

    def label(text, x, baseline, size, role='regular', color=INK, center=None):
        if center is not None:
            x = center - fonts[role].text_length(text, fontsize=size) / 2
        page.insert_text((x, baseline), text, fontname=f'patch_{role}',
                         fontsize=size, color=color, overlay=True)

    def math(expression, x, top, size, color=INK, center=None):
        buf = io.BytesIO()
        math_to_image(expression, buf, prop=FontProperties(size=size),
                      format='pdf', color=color)
        formula = fitz.open(stream=buf.getvalue(), filetype='pdf')
        width, height = formula[0].rect.width, formula[0].rect.height
        if center is not None:
            x = center - width / 2
        page.show_pdf_page(fitz.Rect(x, top, x + width, top + height),
                           formula, 0, overlay=True)
        formula.close()
        return width, height

    # C003.1: DistanceAdj uses pairwise distances between temporal indices.
    # Cover only the incorrect parenthetical label, preserving the graph title.
    cover((1029, 347, 1165, 367), PALE_WHITE)
    label('(temporal distance)', 0, 362, 17, center=1095)

    # C003.2 and C003.3, panel (c): distinguish the headline probability p_j
    # from the semantic logits s^(2) at the existing similarity-scoring output.
    # The adjacent equation specifies the residual adapter unambiguously.
    cover((1059, 479, 1314, 538))
    label('Semantic output', 1067, 495, 20, 'bold', BLUE)
    math(r'$p_j$', 1214, 479, 20, BLUE)
    label('(XD)', 1240, 495, 18, 'regular', BLUE)
    math(r'$p_j=1-\operatorname{softmax}(s_j^{(2)})_{\mathrm{normal}}$',
         0, 496, 17, center=1186)
    math(r'$t_c=u_c+\operatorname{mlp1}(u_c)$',
         0, 522, 17, center=1186)
    # Keep the original adapter box; replace its one-line interior label.
    cover((1175, 652, 1213, 689))
    label('Residual', 0, 665, 12, 'regular', BLUE, center=1194)
    label('mlp1', 0, 684, 18, 'italic', BLUE, center=1194)

    # Panel (d): the pooled feature a contributes once, at u_c=t_c^0+a.
    # Reroute only the original a-return edge from the adapter to that plus.
    # This preserves all existing module positions and avoids implying a
    # second addition of a or a direct, separate adapter input.
    cover((1570, 562, 1735, 573))
    cover((1568, 564, 1582, 606))
    # Original a connector terminates at (1732, 566). Keep that vertical leg,
    # then continue left to the existing plus at (1473, 650).
    page.draw_polyline([(1732, 556), (1732, 566), (1473, 566), (1473, 633)],
                       color=INK, width=1.4, overlay=True)
    arrow = page.new_shape()
    arrow.draw_polyline([(1469, 630), (1473, 638), (1477, 630)])
    arrow.finish(color=INK, fill=INK, closePath=True, width=0.7)
    arrow.commit(overlay=True)

    # Explicit residual definition in the now-clear strip above the adapter.
    math(r'$t_c=u_c+\operatorname{mlp1}(u_c)$',
         0, 582, 21, center=1635)
    cover((1540, 617, 1597, 657))
    label('Residual', 0, 633, 17, 'regular', BLUE, center=1569)
    label('mlp1', 0, 654, 22, 'italic', BLUE, center=1569)

    # Replace only the redundant last footer line (the MIL objective is
    # already stated above panel d) with the same probability readout as c.
    cover((1461, 708, 1781, 729))
    math(r'$p_j=1-\operatorname{softmax}(s_j^{(2)})_{\mathrm{normal}}$',
         0, 704, 20, center=1617)

    # Match the manuscript's original 514.07 pt display width. The PNG stays
    # at its native resolution; new labels/formulae remain embedded vectors.
    final = fitz.open()
    width_pt = 514.07
    output_page = final.new_page(width=width_pt,
                                height=width_pt * SOURCE_SIZE[1] / SOURCE_SIZE[0])
    output_page.show_pdf_page(output_page.rect, doc, 0)
    final.set_metadata({'title': 'Figure 1: locally corrected overview',
                        'subject': 'Temporal graph label; residual text adapter; semantic probability readout',
                        'creator': 'scripts/patch_overview.py',
                        'producer': 'PyMuPDF and Matplotlib'})
    final.save(args.output, garbage=4, deflate=True)
    scale = 2 * SOURCE_SIZE[0] / width_pt
    output_page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).save(args.preview)
    assert sha256(args.source) == before_hash, 'The source image must not change.'
    metadata = {'source': str(args.source), 'source_sha256': before_hash,
                'source_size_px': SOURCE_SIZE, 'output': str(args.output),
                'output_sha256': sha256(args.output), 'preview': str(args.preview),
                'page_size_pt': [output_page.rect.width, output_page.rect.height],
                'mask_regions_in_source_pixels': mask_regions,
                'corrections': ['feature distance -> temporal distance',
                                'explicit residual text adapter in panels c and d',
                                'pooled a edge routed to the existing u_c sum in panel d',
                                'p_j = 1 - softmax(s_j^(2))_normal, distinct from logits'],
                'source_image_unchanged': True}
    args.preview.with_suffix('.json').write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    final.close()
    doc.close()


if __name__ == '__main__':
    main()
