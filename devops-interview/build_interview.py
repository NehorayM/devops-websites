#!/usr/bin/env python3
"""Build the interview-mode question set from the authored open questions.

Reads  isrc/<topic>.py        (every O() call; see qsrc/qlib.py for the shape)
Writes isrc/interview.json    ({"topics","items"})

    python3 build_interview.py            # refuses unless every topic has its full count
    python3 build_interview.py --partial  # while authoring: checks everything but the totals

Each item gets an id hashed from its question, so progress survives reordering and edits
to the model answer; only rewording the question itself starts that item over.
"""
import hashlib
import importlib.util
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent
ISRC = HERE / "isrc"
OUT = ISRC / "interview.json"
sys.path.insert(0, str(HERE / "qsrc"))
from qlib import JM, MS, T, K, TOPICS, SECTIONS, SEC_INDEX, REF_HOSTS, IV_COUNTS, Open  # noqa: E402

HEB = re.compile(r"[֐-׿]")
TOPIC_OF = {s[0]: s[1] for s in SECTIONS}
TOPIC_KEYS = [t[0] for t in TOPICS]


def load():
    items = []
    for f in sorted(ISRC.glob("*.py")):
        spec = importlib.util.spec_from_file_location("isrc_" + f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        got = getattr(mod, "OS", None)
        if not isinstance(got, list):
            sys.exit(f"{f.name}: defines no OS list")
        items.extend(got)
    return items


def norm(t):
    return re.sub(r"\W+", "", t.lower())


def validate(items, partial):
    errs = []
    seen = {}
    for o in items:
        if not isinstance(o, Open):
            errs.append(f"{getattr(o, 'src', '?')}: not an O()")
            continue
        w = o.src
        if o.sec not in SEC_INDEX:
            errs.append(f"{w}: unknown section {o.sec!r}")
        if o.lv not in (JM, MS):
            errs.append(f"{w}: level must be JM or MS")
        if o.kind not in (T, K):
            errs.append(f"{w}: kind must be T or K")
        if len(o.q.strip()) < 25:
            errs.append(f"{w}: question too short")
        if HEB.search(o.q):
            errs.append(f"{w}: the question is asked in English")
        k = norm(o.q)
        if k in seen:
            errs.append(f"{w}: duplicates {seen[k]}")
        seen[k] = w
        if not 3 <= len(o.points) <= 6:
            errs.append(f"{w}: a model answer needs 3–6 points, has {len(o.points)}")
        for p in o.points:
            if not HEB.search(p):
                errs.append(f"{w}: point is not Hebrew: {p[:50]!r}")
            if len(p) > 230:
                errs.append(f"{w}: point too long to scan ({len(p)} chars)")
        if not o.follow or HEB.search(o.follow):
            errs.append(f"{w}: needs an English follow-up question")
        if not o.trap or not HEB.search(o.trap):
            errs.append(f"{w}: needs a Hebrew trap line")
        host = re.sub(r"^https://([^/]+)/?.*$", r"\1", o.ref or "")
        if not (o.ref or "").startswith("https://") or host not in REF_HOSTS:
            errs.append(f"{w}: reference must be https on a documentation host, got {o.ref!r}")

    by = defaultdict(list)
    for o in items:
        if isinstance(o, Open) and o.sec in TOPIC_OF:
            by[TOPIC_OF[o.sec]].append(o)
    for key, want in IV_COUNTS.items():
        got = by[key]
        n = len(got)
        if n > want or (not partial and n != want):
            errs.append(f"{key}: {n} questions, the plan says {want}")
        if n == want:
            t = sum(o.kind == T for o in got)
            jm = sum(o.lv == JM for o in got)
            if abs(t - want / 2) > 2:
                errs.append(f"{key}: {t} troubleshooting of {n}, want about half")
            if abs(jm - want / 2) > 1:
                errs.append(f"{key}: level split {jm}/{n - jm}, want about half each")
    return errs, by


def main():
    partial = "--partial" in sys.argv
    items = load()
    errs, by = validate(items, partial)
    print(f"{len(items)} open questions authored")
    for t in TOPICS:
        got = by[t[0]]
        print(f"  {t[1]:<40} {len(got):>3}/{IV_COUNTS[t[0]]:<3}"
              f"  troubleshooting {sum(o.kind == T for o in got):>3}"
              f"  junior-mid {sum(o.lv == JM for o in got):>3}")
    if errs:
        print(f"\n{len(errs)} problem(s):")
        for e in errs:
            print("  " + e)
        sys.exit(1)

    out = []
    ids = set()
    order = {k: i for i, k in enumerate(TOPIC_KEYS)}
    for o in sorted(items, key=lambda o: (order[TOPIC_OF[o.sec]], SEC_INDEX[o.sec], o.lv)):
        iid = hashlib.sha1(norm(o.q).encode()).hexdigest()[:8]
        assert iid not in ids, f"id collision at {o.src}"
        ids.add(iid)
        out.append({"id": iid, "t": order[TOPIC_OF[o.sec]], "s": SEC_INDEX[o.sec], "lv": o.lv,
                    "k": o.kind, "q": o.q, "p": o.points, "f": o.follow, "w": o.trap, "r": o.ref})
    doc = {"topics": [t[1] for t in TOPICS], "items": out}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(out)} open questions to {OUT.relative_to(HERE)}")


if __name__ == "__main__":
    main()
