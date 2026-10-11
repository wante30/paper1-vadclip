"""Static check without LaTeX: undefined number macros, unresolved \\ref, missing \\input files."""
import glob
import os
import re

os.chdir(os.path.join(os.path.dirname(__file__), "..", "paper"))
defs = set()
for f in ("numbers.tex", "numbers_results.tex"):
    defs |= set(re.findall(r"\\newcommand\{\\(\w+)\}", open(f, encoding="utf-8").read()))
prefixes = ("ucf", "xd", "off", "rel", "proto", "bz", "tMinus", "pre", "post", "eOnly", "cx", "full", "mlp", "pvr")
labels, refs = set(), set()
for f in ["main.tex"] + glob.glob("sections/*.tex") + glob.glob("tables/*.tex"):
    text = "\n".join(line.split("%")[0] for line in open(f, encoding="utf-8").read().splitlines())
    labels |= set(re.findall(r"\\label\{([^}]+)\}", text))
    refs |= set(re.findall(r"\\ref\{([^}]+)\}", text))
    for name in re.findall(r"\\([A-Za-z]+)", text):
        if name.startswith(prefixes) and name not in defs:
            print("UNDEFINED", f, name)
    for inp in re.findall(r"\\input\{([^}]+)\}", text):
        if not os.path.exists(inp if inp.endswith(".tex") else inp + ".tex"):
            print("MISSING INPUT", f, inp)
print("unresolved refs:", sorted(refs - labels) or "none")
