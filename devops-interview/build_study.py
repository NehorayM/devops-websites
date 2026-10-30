#!/usr/bin/env python3
"""Build the Study mode: one quick-reference chapter per interview topic.

Reads  study_src/c*.py   (each exports CHAPTER; block shorthand from learn_src/_h.py)
Writes the #studydata blob inside index.html

Learn mode teaches a subject part by part. Study mode is what you read the evening
before an interview: the commands, the comparison tables, the numbers to remember
and the questions interviewers keep asking, a page per topic, nothing locked.

Every question sector must belong to exactly one chapter: the page shows how much of
the bank a chapter covers, and those shares have to add up to the whole bank.
"""
import importlib.util
import json
import pathlib
import random
import re
import sys
import zlib

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "study_src"
PAGE = HERE / "index.html"
sys.path.insert(0, str(HERE / "learn_src"))     # the block shorthand (_h.py)

BLOCKS = {"h", "p", "list", "steps", "table", "flow", "split", "key", "trap", "note", "code", "dtree", "ask"}
VISUAL = {"table", "flow", "split", "dtree", "code"}
HEB = re.compile(r"[֐-׿]")
# Quiz balance, as in build_learn.py: four options, each with a note of 60+ chars, and lengths that
# don't give the answer away. Before this the right option was the longest in 33 of 46 checks.
NOTE_MIN, SPREAD_MAX, THROWAWAY, RIGHT_MAX, ASK_MIN = 60, 0.40, 0.55, 1.15, 120


def text_of(b):
    t = b["t"]
    if t in ("h", "p", "key", "trap", "note", "code"):
        out = [b["x"]]
    elif t in ("list", "steps", "flow"):
        out = list(b["x"])
    elif t == "ask":
        out = [s for qa in b["x"] for s in qa]
    elif t == "table":
        out = list(b["head"]) + [c for r in b["rows"] for c in r]
    elif t == "split":
        out = [x for c in b["cols"] for x in [c["nm"]] + list(c["items"])]
    elif t == "dtree":
        out = [c for r in b["x"] for c in r]
    else:
        out = []
    return " ".join(out + [b.get("cap", "") or ""])


def check_md(where, s, errs):
    if s.count("**") % 2:
        errs.append(f"{where}: unbalanced ** in {s[:60]!r}")
    if s.count("`") % 2:
        errs.append(f"{where}: unbalanced backtick in {s[:60]!r}")


def load():
    out = []
    for f in sorted(SRC.glob("c*.py")):
        spec = importlib.util.spec_from_file_location("study_" + f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "CHAPTER"):
            sys.exit(f"{f.name}: no CHAPTER")
        out.append((f.name, mod.CHAPTER))
    return out


def sections():
    s = PAGE.read_text(encoding="utf-8")
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', s, re.S)
    return json.loads(m.group(1))["sections"]


def main():
    secnames = sections()
    chapters, errs, owner = [], [], {}
    qn = 0
    for name, c in load():
        w = name
        lacking = [k for k in ("nm", "em", "sub", "dom", "secs", "topics", "quiz") if k not in c]
        if lacking:
            errs.append(f"{w}: missing {', '.join(lacking)}")
            continue
        if not HEB.search(c["sub"]):
            errs.append(f"{w}: the chapter subtitle is Hebrew")
        if c["dom"] not in (0, 1, 2, 3):
            errs.append(f"{w}: dom must be 0-3")
        for s in c["secs"]:
            if not 0 <= s < len(secnames):
                errs.append(f"{w}: sector {s} out of range")
            elif s in owner:
                errs.append(f"{w}: sector {s} already belongs to {owner[s]}")
            owner[s] = w
        words = 0
        for t in c["topics"]:
            tw = f"{w}/{t['nm']}"
            bl = t["blocks"]
            if len(bl) < 4:
                errs.append(f"{tw}: {len(bl)} blocks, want >= 4")
            if not any(b["t"] in VISUAL for b in bl):
                errs.append(f"{tw}: a reference page needs a table, code, flow, split or tree")
            body = ""
            for i, b in enumerate(bl):
                if b["t"] not in BLOCKS:
                    errs.append(f"{tw} block{i}: unknown type {b['t']!r}")
                    continue
                if b["t"] == "table":
                    for r in b["rows"]:
                        if len(r) != len(b["head"]):
                            errs.append(f"{tw} block{i}: ragged row {r}")
                if b["t"] == "ask":
                    for ask_q, ask_a in b["x"]:
                        if len(ask_a.strip()) < ASK_MIN or not HEB.search(ask_a):
                            errs.append(f"{tw} block{i}: {ask_q[:40]!r} needs a Hebrew answer outline of >= {ASK_MIN} chars")
                txt = text_of(b)
                if b["t"] != "code":            # code is shown verbatim, so `**` there is a glob
                    check_md(f"{tw} block{i}", txt, errs)
                body += " " + txt
            if not HEB.search(body):
                errs.append(f"{tw}: no Hebrew in the page")
            if len(body) < 700:
                errs.append(f"{tw}: {len(body)} chars, want >= 700")
            words += len(body.split())
        quiz, tells = [], {"long": 0, "short": 0}
        if len(c["quiz"]) < 3:
            errs.append(f"{w}: {len(c['quiz'])} checks, want >= 3")
        for j, q in enumerate(c["quiz"]):
            qw = f"{w} quiz{j}"
            if not q["q"].rstrip().endswith("?"):
                errs.append(f"{qw}: question does not end with '?'")
            if len(set(q["o"])) != len(q["o"]) or not 3 <= len(q["o"]) <= 5:
                errs.append(f"{qw}: needs 3-5 distinct options")
            if not HEB.search(q.get("x", "")) or len(q.get("x", "")) < 40:
                errs.append(f"{qw}: needs a Hebrew explanation of 40+ chars")
            notes = q.get("w") or [""] * len(q["o"])
            for t in [q["q"], q["x"]] + q["o"] + notes:
                check_md(qw, t, errs)
            if len(q["o"]) != 4:
                errs.append(f"{qw}: {len(q['o'])} options, want 4")
            for k, n in enumerate(notes):
                if len(n.strip()) < NOTE_MIN or not HEB.search(n):
                    errs.append(f"{qw} opt{k}: needs a Hebrew note of >= {NOTE_MIN} chars")
            right, wrong = len(q["o"][0]), [len(o) for o in q["o"][1:]]
            if wrong:
                if right > RIGHT_MAX * max(wrong):
                    errs.append(f"{qw}: right option is {right} chars, over {RIGHT_MAX}x the longest distractor")
                if min(wrong) < THROWAWAY * right:
                    errs.append(f"{qw}: a {min(wrong)}-char distractor is under {THROWAWAY:.0%} of the right option")
                tells["long"] += right > max(wrong)
                tells["short"] += right < min(wrong)
            # the right answer is authored first; spread it across positions (notes move with it)
            pairs = list(zip(q["o"], notes))
            rest = pairs[1:]
            random.Random(zlib.crc32(q["q"].encode())).shuffle(rest)
            at = qn % len(q["o"])
            qn += 1
            order = rest[:at] + [pairs[0]] + rest[at:]
            quiz.append({"q": q["q"], "o": [o for o, _ in order], "w": [n for _, n in order], "a": at, "x": q["x"]})
        for tell, n in tells.items():
            if n > SPREAD_MAX * len(c["quiz"]):
                errs.append(f"{w}: the right option is the {tell}est in {n}/{len(c['quiz'])} checks (max {SPREAD_MAX:.0%})")
        chapters.append({"nm": c["nm"], "em": c["em"], "sub": c["sub"], "dom": c["dom"], "secs": c["secs"],
                         "min": max(3, round(words / 90)),     # tables and commands read slower than prose
                         "topics": [{"nm": t["nm"], "blocks": t["blocks"]} for t in c["topics"]],
                         "quiz": quiz})

    missing = [i for i in range(len(secnames)) if i not in owner]
    if missing:
        errs.append("sectors with no chapter: " + ", ".join(secnames[i] for i in missing))
    if errs:
        print(f"{len(errs)} problem(s) — nothing was written:")
        for e in errs:
            print("  ✗ " + e)
        sys.exit(1)

    blob = json.dumps({"v": 2, "chapters": chapters}, ensure_ascii=False,
                      separators=(",", ":")).replace("</", "<\\/")
    page = PAGE.read_text(encoding="utf-8")
    pat = re.compile(r'(<script id="studydata" type="application/json">).*?(</script>)', re.S)
    if pat.search(page):
        page = pat.sub(lambda m: m.group(1) + blob + m.group(2), page, count=1)
    else:
        anchor = '<script id="data" type="application/json">'
        page = page.replace(anchor, '<script id="studydata" type="application/json">' + blob + '</script>\n' + anchor, 1)
    PAGE.write_text(page, encoding="utf-8")
    print(f"✓ {len(chapters)} chapters · {sum(len(c['topics']) for c in chapters)} topic pages · "
          f"{sum(len(c['quiz']) for c in chapters)} checks · {len(blob) / 1024:.0f} KB")
    for c in chapters:
        print(f"   {c['em']} {c['nm']:<36} {len(c['topics'])} pages · {c['min']:>2} min · sectors {c['secs']}")


if __name__ == "__main__":
    main()
