#!/usr/bin/env python3
"""ivtool.py dump <isrc/file.py> [--short] | apply <isrc/file.py> <fixes.json>: edit open interview questions.

dump prints each O(...) call as JSON: {"i", "q", "p": [points], "f": follow, "w": trap}. With --short it
lists only questions with a trap under 80 chars, a point under 40, or a follow-up without "?".
apply takes [{"i": N, "w"?: "new trap", "f"?: "new follow-up", "p"?: {"<point index>": "new point"}}, ...]
and replaces those string literals in place (positions from ast), so comments, refs and layout survive.
The question text is never touched: an interview question's id is a hash of it, and progress hangs on the id.
"""
import ast
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def calls(src):
    tree = ast.parse(src)
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "O"]


def fields(c):
    kw = {k.arg: k.value for k in c.keywords}
    return {"q": c.args[3], "p": c.args[4], "f": kw.get("follow"), "w": kw.get("trap")}


def dump(path, short=False):
    src = open(path, encoding="utf-8").read()
    out = []
    for i, c in enumerate(calls(src)):
        f = fields(c)
        it = {"i": i, "q": f["q"].value, "p": [e.value for e in f["p"].elts],
              "f": f["f"].value if f["f"] else "", "w": f["w"].value if f["w"] else ""}
        if short and len(it["w"]) >= 80 and all(len(p) >= 40 for p in it["p"]) and it["f"].strip().endswith("?"):
            continue
        out.append(it)
    return out


def apply(path, fixes_path):
    src = open(path, encoding="utf-8").read()
    raw = src.encode("utf-8")
    starts = [0]
    for line in raw.split(b"\n"):
        starts.append(starts[-1] + len(line) + 1)
    cs = calls(src)
    edits = []          # (byte start, byte end, new literal)

    def put(node, text, where):
        assert isinstance(node, ast.Constant) and isinstance(node.value, str), f"{where}: not a plain string literal"
        a = starts[node.lineno - 1] + node.col_offset
        b = starts[node.end_lineno - 1] + node.end_col_offset
        edits.append((a, b, json.dumps(text, ensure_ascii=False).encode("utf-8")))

    fixes = json.load(open(fixes_path, encoding="utf-8"))
    for fx in fixes:
        f = fields(cs[fx["i"]])
        if "w" in fx:
            put(f["w"], fx["w"], f"{fx['i']} trap")
        if "f" in fx:
            put(f["f"], fx["f"], f"{fx['i']} follow")
        for k, text in fx.get("p", {}).items():
            put(f["p"].elts[int(k)], text, f"{fx['i']} point {k}")
    for a, b, new in sorted(edits, reverse=True):
        raw = raw[:a] + new + raw[b:]
    out = raw.decode("utf-8")
    ast.parse(out)
    open(path, "w", encoding="utf-8").write(out)
    print(f"{os.path.basename(path)}: {len(edits)} strings replaced in {len(fixes)} questions")


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        for it in dump(sys.argv[2], "--short" in sys.argv):
            print(json.dumps(it, ensure_ascii=False))
    else:
        apply(sys.argv[2], sys.argv[3])
