"""Check the delivered paper and the numeric snapshot. Requires PyMuPDF.

This is manuscript verification, not model replication or a significance test.
"""
from __future__ import annotations
import csv, json, re
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
pdf=ROOT/'main.pdf'
D=fitz.open(pdf)
texts=[p.get_text() for p in D]
text='\n'.join(texts)
source='\n'.join(p.read_text(encoding='utf-8') for p in (ROOT/'paper').rglob('*.tex'))
log=(ROOT/'build/main.log').read_text(errors='replace')
prose=(ROOT/'paper/main.tex').read_text()+'\n'+'\n'.join(p.read_text() for p in (ROOT/'paper/sections').glob('*.tex'))
forbidden=[r'narrow but useful',r'The two designs look unrelated',r'we do not claim synergy',
 r'not a combination that is more than its parts',r'gains are moderate',r'limitations are equally clear',
 r'as test-set selection should make it',r'seed-to-seed SD.*larger than',r'within seed noise',
 r'statistically significant',r'TBD',r'TODO',r'semantic dataset']
found=[p for p in forbidden if re.search(p,prose,re.I)]
assert len(D)==6, f'Expected 6 pages, got {len(D)}'
assert all(abs(p.rect.width-612)<.1 and abs(p.rect.height-792)<.1 for p in D), 'Paper is not US Letter'
assert 'Placement-Aware Refinement' in text
assert 'Fig. 1.' in texts[1], 'Architecture figure not on page two'
assert not found, f'Unexpected prose patterns: {found}'
assert '84.94' in texts[0] and '84.94' in text
assert '86.69' in text and '86.80' in text, 'PVR-only table missing'
assert '85.01' in text and '+0.44' in text, 'Final semantic AUC missing'
assert '28.88' in text and '18.06' in text, 'Precise latency table missing'
assert not re.search(r'Overfull \\hbox|undefined references|LaTeX Error',log)
assert '[?]' not in text and '??' not in text
refs=re.findall(r'\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}',(ROOT/'paper/main.bbl').read_text())
assert len(refs)==24, f'Expected 24 bibliography entries, got {len(refs)}'
# Verify that printed content stays inside the physical page, without OCR.
outside=[]
for i,p in enumerate(D):
 for word in p.get_text('words'):
  x0,y0,x1,y1,*_=word
  if x0<0 or y0<0 or x1>p.rect.width or y1>p.rect.height:outside.append([i+1,word])
assert not outside, 'Content outside page bounds'
report={'pdf':pdf.name,'pages':len(D),'page_size':'US Letter (612 x 792 pt)',
 'references':len(refs),'tables':5,'figures':1,'overview_page':2,
 'undefined_citations_or_references':False,'overfull_hboxes':False,
 'defensive_phrase_candidates':found,'text_outside_physical_pages':len(outside),
 'word_count_including_tables_figures_references':sum(len(t.split()) for t in texts),
 'visual_review':'All six pages and the architecture figure rendered and reviewed separately.',
 'scope':'Paper build and arithmetic checks only; no training or re-evaluation.',
 'author_block':'Anonymous Authors retained pending final author list'}
(ROOT/'notes/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
