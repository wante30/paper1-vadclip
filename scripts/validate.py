"""Check the delivered paper and the numeric snapshot. Requires PyMuPDF.

This is manuscript verification, not model replication or a significance test.
"""
from __future__ import annotations
import argparse, csv, json, re
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pdf',type=Path,default=ROOT/'main.pdf')
parser.add_argument('--build-dir',type=Path,default=ROOT/'build')
parser.add_argument('--report',type=Path,default=ROOT/'notes/validation.json')
parser.add_argument('--visual-reviewed',action='store_true',
                    help='Record a completed manual review of all rendered pages.')
args=parser.parse_args()
pdf=args.pdf.resolve()
D=fitz.open(pdf)
texts=[p.get_text() for p in D]
text='\n'.join(texts)
source='\n'.join(p.read_text(encoding='utf-8') for p in (ROOT/'paper').rglob('*.tex'))
log=(args.build_dir/'main.log').read_text(encoding='utf-8',errors='replace')
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
assert '0.41' in texts[0], 'Corrected fixed-epoch gain missing from abstract'
assert all(value in text for value in ('86.66','88.25','87.98','+0.35')), 'Corrected UCF results missing'
assert '86.53' not in text, 'Superseded UCF AUC1 still in the compiled manuscript'
assert '0.28' not in text, 'Superseded UCF paired AUC1 gain still in the compiled manuscript'
assert '86.69' in text and '86.80' in text, 'PVR-only table missing'
assert '85.01' in text and '+0.44' in text, 'Final semantic AUC missing'
assert '28.88' in text and '18.06' in text, 'Precise latency table missing'
assert all(value in texts[4] for value in ('77.60','79.15','+1.58')), 'Corrected XD ablation means missing'
assert all(value not in text for value in ('77.44','79.46','79.55')), 'Superseded XD ablation values in manuscript'
assert '79.23' in text and '1.66' in texts[0], 'Unchanged full-method XD result missing'
assert not re.search(r'Overfull \\[hv]box|undefined references|LaTeX Error|Missing character:',log)
assert '[?]' not in text and '??' not in text
refs=re.findall(r'\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}',(args.build_dir/'main.bbl').read_text(encoding='utf-8'))
assert len(refs)==24, f'Expected 24 bibliography entries, got {len(refs)}'
# Verify that printed content stays inside the physical page, without OCR.
outside=[]
for i,p in enumerate(D):
 for word in p.get_text('words'):
  x0,y0,x1,y1,*_=word
  if x0<0 or y0<0 or x1>p.rect.width or y1>p.rect.height:outside.append([i+1,word])
assert not outside, 'Content outside page bounds'
report={'pdf':str(pdf),'pages':len(D),'page_size':'US Letter (612 x 792 pt)',
 'references':len(refs),'tables':5,'figures':1,'overview_page':2,
 'undefined_citations_or_references':False,'overfull_hboxes':False,
 'defensive_phrase_candidates':found,'text_outside_physical_pages':len(outside),
 'word_count_including_tables_figures_references':sum(len(t.split()) for t in texts),
 'visual_review':('All six rendered pages reviewed.' if args.visual_reviewed else 'Pending visual review.'),
 'scope':'Paper build and arithmetic checks only; no training or re-evaluation.',
 'author_block':'Anonymous Authors retained pending final author list'}
args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
