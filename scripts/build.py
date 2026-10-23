"""Rebuild data tables and the IEEE manuscript with the supplied Figure 1.

Usage (from any directory): python scripts/build.py
Requires Python >=3.9 and a TeX installation containing IEEEtran, newtx,
TikZ/standalone, microtype, placeins, needspace, balance, and BibTeX.
No network, training data, model checkpoints, or GPU are required.
"""
from __future__ import annotations
import os, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build'

def run(args: list[str],cwd: Path,log: Path,env=None):
    with log.open('w',encoding='utf-8') as f:
        result=subprocess.run(args,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,env=env)
    if result.returncode:
        lines=log.read_text(encoding='utf-8',errors='replace').splitlines()
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(args)}\n"+'\n'.join(lines[-35:]))

def main():
    BUILD.mkdir(exist_ok=True)
    tex=shutil.which('pdflatex')
    bib=shutil.which('bibtex') or shutil.which('bibtex.original') or shutil.which('bibtex8')
    if not tex or not bib:
        raise RuntimeError('Install a TeX distribution with pdflatex and BibTeX, or compile paper/main.tex on Overleaf.')
    run([sys.executable,str(ROOT/'scripts/make_tables.py')],ROOT,BUILD/'tables_generation.log')
    if not (ROOT/'paper/figures/overview_regenerated.png').is_file():
        raise RuntimeError('Missing regenerated Figure 1: paper/figures/overview_regenerated.png')
    command=[tex,'-interaction=nonstopmode','-halt-on-error',f'-output-directory={BUILD}','main.tex']
    run(command,ROOT/'paper',BUILD/'pass1.log')
    env=dict(os.environ)
    env['BIBINPUTS']=str(ROOT/'refs')+os.pathsep+str(ROOT/'paper')+os.pathsep+env.get('BIBINPUTS','')
    run([bib,'main'],BUILD,BUILD/'bibtex_console.log',env=env)
    run(command,ROOT/'paper',BUILD/'pass2.log')
    run(command,ROOT/'paper',BUILD/'pass3.log')
    log=(BUILD/'main.log').read_text(encoding='utf-8',errors='replace')
    bad=('There were undefined references','Citation `','LaTeX Error','Overfull \\hbox')
    if any(token in log for token in bad):
        raise RuntimeError('The manuscript compiled but a reference/layout error remains. Inspect build/main.log.')
    shutil.copy2(BUILD/'main.pdf',ROOT/'main.pdf')
    shutil.copy2(BUILD/'main.bbl',ROOT/'paper/main.bbl')
    print('Built:',ROOT/'main.pdf')
    print('Tables regenerated from the evidence snapshot and dated author-confirmed corrections; no experiments were run.')

if __name__=='__main__':
    try: main()
    except (OSError,RuntimeError) as error:
        print(error,file=sys.stderr);sys.exit(1)
