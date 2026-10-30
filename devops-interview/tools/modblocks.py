#!/usr/bin/env python3
"""modblocks.py dump <learn_src/sNN.py> <module id> | replace <learn_src/sNN.py> <module id> <blocks.py> [--goal "..."]
Rewrites the teaching part of one Learn module: the blocks list, the 4th argument of MOD(...).
blocks.py holds one Python expression, the new list ([H(...), P(...), ...]), written with the _h.py helpers.
The module's id, name, checks and everything outside the call stay as they are (positions from ast,
converted from UTF-8 byte offsets), and the file is parsed again before it is written. --goal also
replaces the goal line (the 3rd argument). Run build_learn.py afterwards: it checks the result.
"""
import ast, json, sys


def find(src, mid):
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "MOD" and n.args \
                and isinstance(n.args[0], ast.Constant) and n.args[0].value == mid:
            return n
    sys.exit(f"no MOD({mid!r}, ...) in the file")


def span(src, node):
    lines = src.splitlines(keepends=True)
    def off(line, col):
        return sum(len(l) for l in lines[:line - 1]) + len(lines[line - 1].encode()[:col].decode())
    return off(node.lineno, node.col_offset), off(node.end_lineno, node.end_col_offset)


def main(a):
    if len(a) < 3 or a[0] not in ("dump", "replace"):
        sys.exit(__doc__)
    path, mid = a[1], a[2]
    src = open(path, encoding="utf-8").read()
    call = find(src, mid)
    s, e = span(src, call.args[3])
    if a[0] == "dump":
        print(src[s:e])
        return
    new = open(a[3], encoding="utf-8").read().strip()
    if not isinstance(ast.parse(new, mode="eval").body, ast.List):
        sys.exit("blocks file must hold one list expression")
    edits = [(s, e, new)]
    if "--goal" in a:
        g = call.args[2]
        gs, ge = span(src, g)
        edits.append((gs, ge, json.dumps(a[a.index("--goal") + 1], ensure_ascii=False)))
    for s0, e0, txt in sorted(edits, reverse=True):
        src = src[:s0] + txt + src[e0:]
    ast.parse(src)
    open(path, "w", encoding="utf-8").write(src)
    print(f"{path}: module {mid} replaced ({len(new)} chars of source)")


if __name__ == "__main__":
    main(sys.argv[1:])
