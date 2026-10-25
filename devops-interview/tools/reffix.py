#!/usr/bin/env python3
"""reffix.py <fixes.json> [--dry]: rewrite ref= links in qsrc/*.py and isrc/*.py.

fixes.json maps an old URL, exactly as the bank shows it, to the new one: {"https://old": "https://new", ...}
(linkcheck.py --out writes a report whose MOVED/ANCHOR entries carry "new"; turn those into this map).
Each `ref=` argument is evaluated with the file's own constants (refs are often written D+"path"), and when
its value is in the map the whole argument is replaced by the new URL as a plain string literal. Positions
come from ast, so comments and layout survive. Refs only feed q.r, so BANKV and progress are untouched.
"""
import ast, json, os, sys, glob

fixes = json.load(open(sys.argv[1]))
DRY = "--dry" in sys.argv
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
done = set()
total = 0
for path in sorted(glob.glob(os.path.join(ROOT, "qsrc", "*.py")) + glob.glob(os.path.join(ROOT, "isrc", "*.py"))):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    # the file's string constants (D = "https://...", and so on), to evaluate D+"path"
    env = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                env[node.targets[0].id] = eval(compile(ast.Expression(node.value), path, "eval"), {}, dict(env))
            except Exception:
                pass
    lines = src.split("\n")
    starts = [0]
    for l in lines:
        starts.append(starts[-1] + len(l.encode("utf-8")) + 1)
    data = src.encode("utf-8")
    edits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg != "ref":
                continue
            try:
                val = eval(compile(ast.Expression(kw.value), path, "eval"), {}, dict(env))
            except Exception:
                continue
            if val in fixes:
                a = starts[kw.value.lineno - 1] + kw.value.col_offset
                b = starts[kw.value.end_lineno - 1] + kw.value.end_col_offset
                edits.append((a, b, json.dumps(fixes[val]), val))
    for a, b, new, old in sorted(edits, reverse=True):
        data = data[:a] + new.encode("utf-8") + data[b:]
        done.add(old)
    if edits:
        total += len(edits)
        print("%-28s %d ref(s)" % (os.path.relpath(path, ROOT), len(edits)))
        if not DRY:
            out = data.decode("utf-8")
            ast.parse(out)                                     # still valid Python
            open(path, "w", encoding="utf-8").write(out)
print("replaced", total, "refs;", len(set(fixes) - done), "map entries matched nothing:")
for u in sorted(set(fixes) - done):
    print("  ", u)
