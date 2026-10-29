#!/usr/bin/env python3
"""bankfix.py show <bank-index ...> | apply <fixes.json>: edit exam questions by their index in qsrc/bank.json.

The bank is built in a shuffled order, so an index from the page, QA or contentlint doesn't say
which qsrc file holds the question. This finds it by the stem, then rewrites the Q(...) call
through qtool.write, so the right option stays first and comments outside the call survive.

fixes.json: a list of {"b": <bank index>, and any of
    "q":  "new stem",
    "o":  {"<current option text>": "new option text", ...},
    "y":  {"<current option text>": "new Hebrew line", ...},
    "x":  "new tip"}
Option keys are the option text as it is now (before this fix), so a fix can't hit the wrong option.
Refs are changed with tools/reffix.py. Rebuild with build_bank.py and inject_bank.py after.
"""
import json, os, re, sys, tempfile, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from qtool import dump, write  # noqa: E402

ROOT = os.path.join(HERE, "..")
QS = json.load(open(os.path.join(ROOT, "qsrc", "bank.json"), encoding="utf-8"))["questions"]
key = lambda s: re.sub(r"\W+", "", s.lower())


def locate():
    loc = {}
    for n in sorted(os.listdir(os.path.join(ROOT, "qsrc"))):
        if n.endswith(".py") and n != "qlib.py" and not n.startswith("_"):
            for it in dump(n):
                loc[key(it["q"])] = (n, it["i"])
    return loc


def show(idx):
    loc = locate()
    for b in idx:
        q = QS[b]; n, i = loc[key(q["q"])]
        print(f"== b{b} {n}:{i} [{q['lv'] and 'MS' or 'JM'} {q['k']}] {q['q']}")
        for k, (L, t) in enumerate(q["o"]):
            print(f"   {'R' if L in q['a'] else ' '} {t}")
            print(f"       {q['y'][k][:160]}")
        print(f"   tip: {q['x'][:160]}")


def apply(path):
    fixes = json.load(open(path, encoding="utf-8"))
    loc = locate()
    per = collections.defaultdict(list)
    for f in fixes:
        n, i = loc[key(QS[f["b"]]["q"])]
        per[n].append((i, f))
    total = 0
    for n, items in per.items():
        d = {it["i"]: it for it in dump(n)}
        out = []
        for i, f in items:
            e = d[i]
            opts = [e["r"]] + e["w"]
            for old, new in f.get("o", {}).items():
                hit = [o for o in opts if o[0] == old]
                assert len(hit) == 1, f"b{f['b']}: option not found: {old!r}"
                hit[0][0] = new
            for old, new in f.get("y", {}).items():
                new_t = f.get("o", {}).get(old, old)
                hit = [o for o in opts if o[0] in (old, new_t)]
                assert len(hit) == 1, f"b{f['b']}: option for why not found: {old!r}"
                hit[0][1] = new
            if "x" in f:
                e["tip"] = f["x"]
            ent = {"i": i, "r": opts[0], "w": opts[1:], "tip": e["tip"]}
            if "q" in f:
                ent["q"] = f["q"]
            out.append(ent)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as t:
            json.dump(out, t, ensure_ascii=False)
        write(n, t.name)
        os.unlink(t.name)
        total += len(out)
    print(f"applied {len(fixes)} fixes to {total} questions in {len(per)} files")


if __name__ == "__main__":
    if sys.argv[1] == "show":
        show([int(x) for x in sys.argv[2:]])
    else:
        apply(sys.argv[2])
