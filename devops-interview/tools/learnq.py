#!/usr/bin/env python3
"""learnq.py dump <learn_src/sNN.py> | apply <learn_src/sNN.py> <fixes.json> | stats <learn_src/sNN.py ...>

Edits a Learn subject's questions: the checks after each module (C) and the final exam (F),
or a Study chapter's quiz (QZ, keys z0, z1, ...).
dump prints one JSON object per question, in source order:
    {"k": "c3" or "f7", "m": module id (finals only), "q": stem, "o": [[text, why], ...], "x": explanation}
with the right option first, as the source writes it.
apply takes [{"k": ..., "o": [[text, why], ...] (right first), and optionally "q" and "x"}, ...] and
rewrites each whole call in place (positions from ast), so modules, recaps and comments survive.
stats prints what build_learn.py enforces on questions: right option longest/shortest per subject,
throwaway distractors, option count and short notes.
askdump / askapply <file> <answers.json> do the same for ASK blocks (Learn or Study files): answers.json
maps each question, exactly as written, to its Hebrew answer outline; the item becomes (question, answer).
"""
import ast
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def calls(src):
    tree = ast.parse(src)
    out = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") in ("C", "F", "QZ")]
    return sorted(out, key=lambda n: (n.lineno, n.col_offset))


def lit(node):
    return ast.literal_eval(node)


def parse(c):
    kw = {k.arg: lit(k.value) for k in c.keywords}
    args = [lit(a) for a in c.args]
    if c.func.id == "F":
        m, q, opts = args[0], args[1], args[2:]
    else:
        m, q, opts = None, args[0], args[1:]
    opts = [list(o) if isinstance(o, tuple) else [o, ""] for o in opts]
    return m, q, opts, kw.get("x", "")


def dump(path):
    src = open(path, encoding="utf-8").read()
    out, nc, nf = [], 0, 0
    for c in calls(src):
        m, q, opts, x = parse(c)
        if c.func.id in ("C", "QZ"):
            k, nc = f"{'c' if c.func.id == 'C' else 'z'}{nc}", nc + 1
        else:
            k, nf = f"f{nf}", nf + 1
        it = {"k": k, "q": q, "o": opts, "x": x}
        if m:
            it["m"] = m
        out.append(it)
    return out


def render(kind, m, q, opts, x, col):
    j = lambda s: json.dumps(s, ensure_ascii=False)
    pad = " " * (col + 2)
    head = f"{kind}({j(m)}, {j(q)}," if kind == "F" else f"{kind}({j(q)},"
    lines = [head] + [f"{pad}({j(t)}, {j(w)})," for t, w in opts] + [f"{pad}x={j(x)})"]
    return "\n".join(lines)


def apply(path, fixes_path):
    src = open(path, encoding="utf-8").read()
    raw = src.encode("utf-8")
    starts = [0]
    for line in raw.split(b"\n"):
        starts.append(starts[-1] + len(line) + 1)
    by_key = {}
    nc = nf = 0
    for c in calls(src):
        if c.func.id in ("C", "QZ"):
            by_key[f"{'c' if c.func.id == 'C' else 'z'}{nc}"] = c
            nc += 1
        else:
            by_key[f"f{nf}"] = c
            nf += 1
    edits = []
    fixes = json.load(open(fixes_path, encoding="utf-8"))
    for fx in fixes:
        c = by_key[fx["k"]]
        m, q, opts, x = parse(c)
        q, x = fx.get("q", q), fx.get("x", x)
        new_opts = fx.get("o", opts)
        assert all(isinstance(o, list) and len(o) == 2 for o in new_opts), fx["k"]
        a = starts[c.lineno - 1] + c.col_offset
        b = starts[c.end_lineno - 1] + c.end_col_offset
        edits.append((a, b, render(c.func.id, m, q, new_opts, x, c.col_offset).encode("utf-8")))
    for a, b, new in sorted(edits, reverse=True):
        raw = raw[:a] + new + raw[b:]
    out = raw.decode("utf-8")
    ast.parse(out)
    open(path, "w", encoding="utf-8").write(out)
    print(f"{os.path.basename(path)}: rewrote {len(edits)} questions")


def stats(paths):
    for p in paths:
        qs = dump(p)
        longest = shortest = throw = short = not4 = 0
        for it in qs:
            lens = [len(t) for t, _ in it["o"]]
            r, w = lens[0], lens[1:]
            longest += r > max(w)
            shortest += r < min(w)
            throw += sum(1 for n in w if n < 0.55 * r)
            short += sum(1 for _, why in it["o"] if len(why.strip()) < 60)
            not4 += len(lens) != 4
        n = len(qs)
        print(f"{os.path.basename(p):22} q={n} longest={longest} ({longest / n:.0%}) shortest={shortest} "
              f"({shortest / n:.0%}) throwaway={throw} short-notes={short} not-4={not4}")


def asks(src):
    tree = ast.parse(src)
    out = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "ASK"]
    return sorted(out, key=lambda n: (n.lineno, n.col_offset))


def askdump(path):
    src = open(path, encoding="utf-8").read()
    return [lit(a) for c in asks(src) for a in c.args]


def askapply(path, answers_path):
    src = open(path, encoding="utf-8").read()
    raw = src.encode("utf-8")
    starts = [0]
    for line in raw.split(b"\n"):
        starts.append(starts[-1] + len(line) + 1)
    ans = json.load(open(answers_path, encoding="utf-8"))
    edits, used = [], set()
    for c in asks(src):
        for a in c.args:
            v = lit(a)
            q = v[0] if isinstance(v, tuple) else v
            if q in ans:
                used.add(q)
                b0 = starts[a.lineno - 1] + a.col_offset
                b1 = starts[a.end_lineno - 1] + a.end_col_offset
                new = "(" + json.dumps(q, ensure_ascii=False) + ",\n" + " " * (a.col_offset + 1) + json.dumps(ans[q], ensure_ascii=False) + ")"
                edits.append((b0, b1, new.encode("utf-8")))
    missing = set(ans) - used
    assert not missing, f"questions not found: {sorted(missing)}"
    for b0, b1, new in sorted(edits, reverse=True):
        raw = raw[:b0] + new + raw[b1:]
    out = raw.decode("utf-8")
    ast.parse(out)
    open(path, "w", encoding="utf-8").write(out)
    print(f"{os.path.basename(path)}: {len(edits)} answer outlines")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "dump":
        for it in dump(sys.argv[2]):
            print(json.dumps(it, ensure_ascii=False))
    elif cmd == "apply":
        apply(sys.argv[2], sys.argv[3])
    elif cmd == "askdump":
        for it in askdump(sys.argv[2]):
            print(json.dumps(it, ensure_ascii=False))
    elif cmd == "askapply":
        askapply(sys.argv[2], sys.argv[3])
    else:
        stats(sys.argv[2:])
