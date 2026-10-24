# -*- coding: utf-8 -*-
"""Shorthand for authoring Learn subjects (learn_src/sNN_*.py).

Lesson text is Hebrew with technical terms in English; questions and options are English;
every explanation (x) and per-option note (w) is Hebrew — the same split as the question bank.
The correct option is always written first; build_learn.py spreads answers across positions.
"""


def H(x): return {"t": "h", "x": x}
def P(x): return {"t": "p", "x": x}
def UL(*x): return {"t": "list", "x": list(x)}
def STEPS(*x): return {"t": "steps", "x": list(x)}
def KEY(x): return {"t": "key", "x": x}
def TRAP(x): return {"t": "trap", "x": x}
def NOTE(x): return {"t": "note", "x": x}


def TABLE(head, *rows, cap=None):
    b = {"t": "table", "head": list(head), "rows": [list(r) for r in rows]}
    if cap:
        b["cap"] = cap
    return b


def FLOW(*x, cap=None):
    b = {"t": "flow", "x": list(x)}
    if cap:
        b["cap"] = cap
    return b


def SPLIT(*cols, cap=None):
    b = {"t": "split", "cols": [{"nm": nm, "items": list(items)} for nm, items in cols]}
    if cap:
        b["cap"] = cap
    return b


def CODE(x, cap=None):
    b = {"t": "code", "x": x.strip("\n")}
    if cap:
        b["cap"] = cap
    return b


def TREE(*rows, cap=None):
    b = {"t": "dtree", "x": [list(r) for r in rows]}
    if cap:
        b["cap"] = cap
    return b


def MOD(id, nm, goal, blocks, checks, min=8):
    return {"id": id, "nm": nm, "goal": goal, "min": min, "blocks": blocks, "checks": checks}


def C(q, right, *wrong, x):
    """A check question after a module: options are plain strings, the right one first."""
    return {"q": q, "o": [right] + list(wrong), "a": [0], "x": x}


def F(m, q, right, *wrong, x):
    """A final-exam question: each option is (text, why in Hebrew), the right one first."""
    return {"q": q, "o": [{"t": t, "w": w} for t, w in [right] + list(wrong)], "a": [0], "x": x, "m": m}
