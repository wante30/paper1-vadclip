"""Print the nested key structure of JSON result files (read-only helper)."""
import json
import sys


def shape(obj, depth=0, max_depth=3, key=""):
    pad = "  " * depth
    if isinstance(obj, dict):
        keys = list(obj.keys())
        print(f"{pad}{key} dict[{len(keys)}]: {keys[:14]}")
        if depth < max_depth:
            for k in keys[:6]:
                shape(obj[k], depth + 1, max_depth, k)
    elif isinstance(obj, list):
        print(f"{pad}{key} list[{len(obj)}]")
        if obj and depth < max_depth:
            shape(obj[0], depth + 1, max_depth, "[0]")
    else:
        print(f"{pad}{key} = {repr(obj)[:90]}")


for path in sys.argv[1:]:
    print("=====", path)
    with open(path, encoding="utf-8-sig") as handle:
        shape(json.load(handle))
