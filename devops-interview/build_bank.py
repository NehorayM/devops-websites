#!/usr/bin/env python3
"""Build the Ship It question bank from the authored questions.

Reads  qsrc/<topic>.py   (every Q() call; see qsrc/qlib.py for the shape)
Writes qsrc/bank.json    ({"sections","short","topics","questions"})

The bank is written in paper order: questions 0–64 are Exam 1, 65–129 Exam 2, and so on,
because the page cuts papers straight out of the bank. Papers 1–10 are Junior–Mid and
11–20 Mid–Senior, and every paper carries each topic in proportion to its weight.

    python3 build_bank.py            # refuses unless the whole syllabus is written
    python3 build_bank.py --partial  # while authoring: checks everything but the totals

The build refuses anything that would reach a learner broken: a missing or duplicate
option, an explanation that is not Hebrew, a reference outside the documentation hosts,
a duplicate question, or a topic whose troubleshooting/knowledge or level split is off.
"""
import importlib.util
import json
import pathlib
import random
import re
import sys
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent
QSRC = HERE / "qsrc"
OUT = QSRC / "bank.json"
sys.path.insert(0, str(QSRC))
from qlib import JM, MS, T, K, TOPICS, SECTIONS, SEC_INDEX, REF_HOSTS, Question  # noqa: E402

LETTERS = "ABCD"
PAPER_LEN = 65
HEB = re.compile(r"[֐-׿]")
SEED = 20261024


def load():
    qs = []
    for f in sorted(QSRC.glob("*.py")):
        if f.name == "qlib.py":
            continue
        spec = importlib.util.spec_from_file_location("qsrc_" + f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        got = getattr(mod, "QS", None)
        if not isinstance(got, list):
            sys.exit(f"{f.name}: defines no QS list")
        qs.extend(got)
    return qs


def norm(t):
    return re.sub(r"\W+", "", t.lower())


def validate(qs, partial):
    errs = []
    seen = {}
    for q in qs:
        where = q.src
        if not isinstance(q, Question):
            errs.append(f"{where}: not a Q()")
            continue
        if q.sec not in SEC_INDEX:
            errs.append(f"{where}: unknown section {q.sec!r}")
        if q.lv not in (JM, MS):
            errs.append(f"{where}: level must be JM or MS")
        if q.kind not in (T, K):
            errs.append(f"{where}: kind must be T or K")
        if len(q.q.strip()) < 25:
            errs.append(f"{where}: stem too short")
        k = norm(q.q)
        if k in seen:
            errs.append(f"{where}: duplicates {seen[k]}")
        seen[k] = where
        if len(q.opts) != 4:
            errs.append(f"{where}: needs exactly 4 options, has {len(q.opts)}")
        texts = []
        for o in q.opts:
            if not (isinstance(o, tuple) and len(o) == 2 and all(isinstance(x, str) for x in o)):
                errs.append(f"{where}: an option must be (text, why)")
                continue
            txt, why = o
            if not txt.strip():
                errs.append(f"{where}: empty option")
            if not HEB.search(why):
                errs.append(f"{where}: option {txt[:30]!r} has no Hebrew explanation")
            texts.append(norm(txt))
        if len(set(texts)) != len(texts):
            errs.append(f"{where}: duplicate options")
        if not HEB.search(q.tip or ""):
            errs.append(f"{where}: interview tip missing or not Hebrew")
        host = re.match(r"https://([^/]+)/", q.ref or "")
        if not host or host.group(1) not in REF_HOSTS:
            errs.append(f"{where}: ref must be https on a documentation host, got {q.ref!r}")
        # a correct answer that is visibly the longest gives itself away
        lens = [len(o[0]) for o in q.opts]
        if lens[0] > 1.9 * max(lens[1:]) and lens[0] > 60:
            errs.append(f"{where}: the correct option is far longer than every distractor")

    by_topic = defaultdict(list)
    by_sec = Counter(q.sec for q in qs)
    topic_of = {s[0]: s[1] for s in SECTIONS}
    for q in qs:
        by_topic[topic_of.get(q.sec)].append(q)
    report = []
    for key, name, _w, count, lv0 in TOPICS:
        got = by_topic.get(key, [])
        n = len(got)
        t = sum(1 for q in got if q.kind == T)
        j = sum(1 for q in got if q.lv == JM)
        report.append(f"  {name:40s} {n:4d}/{count:<4d} troubleshooting {t:4d}  junior-mid {j:4d}/{lv0}")
        if n > count:
            errs.append(f"{name}: {n} questions, the plan says {count}")
        if j > lv0 or n - j > count - lv0:
            errs.append(f"{name}: level split {j}/{n - j}, the plan says {lv0}/{count - lv0}")
        if not partial:
            if n != count:
                errs.append(f"{name}: {n} questions, the plan says {count}")
            if abs(t - count / 2) > 2:
                errs.append(f"{name}: {t} troubleshooting of {n} — should be half (±2)")
    for slug, _t, nm, _s, count in SECTIONS:
        if by_sec[slug] > count or (not partial and by_sec[slug] != count):
            errs.append(f"{nm}: {by_sec[slug]} questions, the plan says {count}")
    return errs, report


def compose(qs):
    """Deal the questions into papers: Junior–Mid first, then Mid–Senior.

    Within a level the questions are sorted by topic and dealt one at a time onto the
    papers in turn, so each paper gets the same share of every topic (±1) and exactly
    PAPER_LEN questions. Each paper is then shuffled so topics interleave.
    """
    rng = random.Random(SEED)
    order = {s[0]: i for i, s in enumerate(SECTIONS)}
    out = []
    for lv in (JM, MS):
        group = sorted((q for q in qs if q.lv == lv), key=lambda q: (order[q.sec], q.src))
        npapers = max(1, -(-len(group) // PAPER_LEN))
        papers = [[] for _ in range(npapers)]
        for i, q in enumerate(group):
            papers[i % npapers].append(q)
        for p in papers:
            rng.shuffle(p)
            out.extend(p)
    return out


def place(qs):
    """Put the correct option at a balanced position and shuffle the distractors."""
    rng = random.Random(SEED + 1)
    slots = [i % 4 for i in range(len(qs))]
    rng.shuffle(slots)
    out = []
    for q, pos in zip(qs, slots):
        wrong = q.opts[1:]
        rng.shuffle(wrong)
        opts = wrong[:pos] + [q.opts[0]] + wrong[pos:]
        out.append({
            "s": SEC_INDEX[q.sec],
            "q": q.q.strip(),
            "o": [[LETTERS[i], o[0].strip()] for i, o in enumerate(opts)],
            "a": [LETTERS[pos]],
            "y": [o[1].strip() for o in opts],
            "x": q.tip.strip(),
            "lv": q.lv,
            "k": q.kind,
            "r": q.ref,
        })
    return out


def main():
    partial = "--partial" in sys.argv
    qs = load()
    errs, report = validate(qs, partial)
    print(f"{len(qs)} questions authored")
    print("\n".join(report))
    if errs:
        print(f"\n{len(errs)} problem(s):")
        for e in errs[:80]:
            print("  " + e)
        sys.exit(1)
    bank = place(compose(qs))
    pos = Counter(q["a"][0] for q in bank)
    print("correct-answer positions:", dict(sorted(pos.items())))
    OUT.write_text(json.dumps({
        "sections": [s[2] for s in SECTIONS],
        "short": [s[3] for s in SECTIONS],
        "topics": [{"key": t[0], "nm": t[1], "w": t[2],
                    "secs": [i for i, s in enumerate(SECTIONS) if s[1] == t[0]]} for t in TOPICS],
        "questions": bank,
    }, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"wrote {len(bank)} questions to {OUT.relative_to(HERE)}")


if __name__ == "__main__":
    main()
