#!/usr/bin/env python3
"""Rewrite questions in a qsrc file without touching stems, levels, kinds or refs.

    python3 tools/qtool.py dump  k8s_pods.py            # JSON: [{i, lv, kind, q, r:[text,why], w:[[text,why]x3], tip, ref}]
    python3 tools/qtool.py write k8s_pods.py new.json   # replace Q(...) calls with the JSON's options, whys and tip
    python3 tools/qtool.py stats [k8s_pods.py ...]       # how often the right answer is the longest, short whys

new.json is a list of {i, r, w, tip} (optionally q to reword the stem). Questions not listed stay as they are.
The right option stays first in the source; build_bank.py places it.
"""
import ast, json, pathlib, sys

QSRC = pathlib.Path(__file__).resolve().parent.parent / "qsrc"


def calls(src):
    t = ast.parse(src)
    return sorted((n for n in ast.walk(t) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "Q"),
                  key=lambda n: n.lineno)


def seg(src, n):
    return ast.get_source_segment(src, n)


def dump(name):
    src = (QSRC / name).read_text(encoding="utf-8")
    res = []
    for i, n in enumerate(calls(src)):
        a = n.args
        kw = {k.arg: k.value for k in n.keywords}
        res.append({"i": i, "lv": seg(src, a[1]), "kind": seg(src, a[2]), "q": ast.literal_eval(a[3]),
                    "r": list(ast.literal_eval(a[4])), "w": [list(ast.literal_eval(x)) for x in a[5:]],
                    "tip": ast.literal_eval(kw["tip"]) if "tip" in kw else "",
                    "ref": seg(src, kw["ref"]) if "ref" in kw else ""})
    return res


def lit(s):
    return json.dumps(s, ensure_ascii=False)


def write(name, newf):
    p = QSRC / name
    src = p.read_text(encoding="utf-8")
    old_lines = src.split("\n")
    lines = list(old_lines)
    new = {d["i"]: d for d in json.load(open(newf, encoding="utf-8"))}
    ns = calls(src)
    for i in sorted(new, reverse=True):
        n, d = ns[i], new[i]
        a = n.args
        kw = {k.arg: k.value for k in n.keywords}
        assert len(d["w"]) == 3, (i, "need 3 wrong options")
        stem = d.get("q") or ast.literal_eval(a[3])
        out = [f"Q({seg(src, a[0])}, {seg(src, a[1])}, {seg(src, a[2])},", f"  {lit(stem)},"]
        for t, w in [d["r"]] + d["w"]:
            out += [f"  ({lit(t)},", f"   {lit(w)}),"]
        out.append(f"  tip={lit(d['tip'])}," if "ref" in kw else f"  tip={lit(d['tip'])})")
        if "ref" in kw:
            out.append(f"  ref={seg(src, kw['ref'])})")
        tail = old_lines[n.end_lineno - 1].encode()[n.end_col_offset:].decode()
        out[-1] += tail
        lines[n.lineno - 1:n.end_lineno] = out
    p.write_text("\n".join(lines), encoding="utf-8")
    ast.parse(p.read_text(encoding="utf-8"))
    print(f"{name}: rewrote {len(new)} questions")


def stats(names):
    tot = longest = 0
    for name in names:
        qs = dump(name)
        lg = sum(1 for d in qs if len(d["r"][0]) > max(len(w[0]) for w in d["w"]))
        short = sum(1 for d in qs for o in [d["r"]] + d["w"] if len(o[1]) < 60)
        tot += len(qs); longest += lg
        print(f"  {name:18s} right-is-longest {lg:3d}/{len(qs):<3d} ({100 * lg // max(1, len(qs)):2d}%)  whys<60ch {short}")
    print(f"  {'total':18s} right-is-longest {longest}/{tot} ({100 * longest // max(1, tot)}%)")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "dump":
        print(json.dumps(dump(sys.argv[2]), ensure_ascii=False, indent=1))
    elif cmd == "write":
        write(sys.argv[2], sys.argv[3])
    else:
        stats(sys.argv[2:] or sorted(p.name for p in QSRC.glob("*.py") if p.name != "qlib.py"))
