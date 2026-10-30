#!/usr/bin/env python3
"""contentlint.py [--strict]: measure content quality across the bank, interview mode, Learn and Study.

Every line is one measurable defect from the October 2026 audit, with the most it may
still count. Run it after any content change; --strict exits non-zero when a line is over
its limit, so a regression can't slip through. (Builders enforce some of the same rules
per file; this is the bank-wide view, and the place for rules no single builder sees.)
"""
import collections
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "learn_src"))
import build_learn as BL  # noqa: E402

QS = json.load(open(os.path.join(ROOT, "qsrc", "bank.json"), encoding="utf-8"))["questions"]
IV = json.load(open(os.path.join(ROOT, "isrc", "interview.json"), encoding="utf-8"))["items"]
HTML = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
STOP = {"what", "how", "why", "the", "and", "does", "with", "which", "that", "this", "for", "are",
        "from", "you", "your", "its", "into", "when", "than", "then", "not", "but", "use", "using"}


def words(s):
    return set(re.findall(r"[a-z0-9_.\-/]{3,}", re.sub(r"`", "", s.lower())))


def right_index(q):
    return [k for k, (L, _) in enumerate(q["o"]) if L in q["a"]][0]


rows = []          # (area, item, count, limit, examples)


def row(area, item, hits, limit):
    rows.append((area, item, len(hits), limit, hits[:4]))


# ---------------- exam bank ----------------
ABS = re.compile(r"\b(always|never|all|every|only|any|completely|entirely|guarantees?)\b", re.I)
code_only_right, code_all_but, absolute, echo = [], [], [], []
for i, q in enumerate(QS):
    ot = [t for _, t in q["o"]]
    r = right_index(q)
    ticks = ["`" in t for t in ot]
    if ticks[r] and sum(ticks) == 1:
        code_only_right.append(i)
    if not ticks[r] and sum(ticks) == 3:
        code_all_but.append(i)
    if all(ABS.search(ot[k]) for k in range(4) if k != r) and not ABS.search(ot[r]):
        absolute.append(i)
    sw = words(q["q"]) - STOP
    only = {w for w in (words(ot[r]) & sw) - set().union(*[words(ot[k]) & sw for k in range(4) if k != r]) if len(w) > 4}
    if len(only) >= 2:
        echo.append((i, sorted(only)[:3]))
row("bank", "#11 only the right option has `code`", code_only_right, 12)
row("bank", "#11 every option but the right one has `code`", code_all_but, 3)
row("bank", "#12 three absolute-word distractors, right one hedged", absolute, 3)
row("bank", "#13 right option echoes 2+ stem words no distractor uses", echo, 8)

pairs = []
norm = [words(q["q"]) | words(" ".join(t for L, t in q["o"] if L in q["a"])) for q in QS]
for a in range(len(QS)):
    for b in range(a + 1, len(QS)):
        u = norm[a] | norm[b]
        if u and len(norm[a] & norm[b]) / len(u) > 0.6:
            pairs.append((a, b))
row("bank", "#14 near-duplicate question pairs", pairs, 0)

# Roots that are the document itself, checked against each site's source: the manifesto is one page,
# Stryker's docs root is its "What is mutation testing?" page (slug '/'), conftest's root is its overview.
ONE_PAGE = {"https://principlesofchaos.org/", "https://stryker-mutator.io/docs/", "https://www.conftest.dev/"}
landing = [(i, q["r"]) for i, q in enumerate(QS) if q["r"] not in ONE_PAGE and
           (re.match(r"^https://[^/]+/?$", q["r"]) or re.search(r"/docs/?$|/en/stable/?$|/doc/?$", q["r"]))]
row("bank", "#20 doc link is a landing page", landing, 0)


# ---------------- facts and hygiene, everywhere ----------------
def all_texts():
    for i, q in enumerate(QS):
        yield f"q{i}", " ".join([q["q"]] + [t for _, t in q["o"]] + q["y"] + [q["x"]])
    for it in IV:
        yield f"iv:{it['id']}", " ".join([it["q"]] + it["p"] + [it.get("f", ""), it.get("w", "")])
    for d in ("learn_src", "study_src"):
        for f in sorted(os.listdir(os.path.join(ROOT, d))):
            if f.endswith(".py") and not f.startswith("_"):
                yield f"{d}/{f}", open(os.path.join(ROOT, d, f), encoding="utf-8").read()


STALE = [
    ("#17 Argo CD polling stated as 3 min / 180 s",
     r"(reconcil|polling|בודק את Git|Argo CD בודק)[^.\n]{0,80}(3 דקות|שלוש דקות|180 ?(s|שניות)|three minutes|3 minutes)"
     r"|(ברירת המחדל היא 3 דקות|הערך הרגיל הוא 180 שניות|הוא 180 שניות כברירת מחדל|כל כ-3 דקות)"),
    ("#15 seccomp default said to change after 1.27", r"עד 1\.27 ברירת המחדל הייתה Unconfined"),
    ("#16 chroot /host said to work in a plain kubectl debug node pod", r"עם `chroot /host` אפשר להריץ כלים של ה-node, בלי SSH"),
    ("#18 Ingress NGINX described as merely shrinking / current default", r"התחזוקה של ingress-nginx מצטמצמת"),
    ("#19 create-only/create-update said to block all deletions", r"`applicationsSync: create-only` או `create-update` חוסם מחיקות"),
    # found while rewriting interview mode, checked against the Helm 3 and Argo CD docs sources
    ("#19b a hook with no delete policy said to block the next run (default is before-hook-creation)",
     r"בלי hook-delete-policy, Job של hook נשאר\. הוא יתנגש|אם לא מגדירים policy, ה-hook נשאר עד שמוחקים"
     r"|בלי policy, ה-hook פשוט נשאר|Job בלי `hook-delete-policy: before-hook-creation` נשאר|לשכוח `hook-delete-policy`, כך שה-Job"),
    ("#19c `helm --wait` said to wait for Jobs (that needs --wait-for-jobs)", r"--wait`[^\n]{0,40}ה-Jobs יסתיימו"),
    ("#19d `Replace=true` said to delete and recreate (only Force=true does)",
     r"Replace מוחק ויוצר|Replace ימחק וייצור|`Replace=true` או Force sync מוחקים|\(או delete ו-create\)|\"Replace=true\", \"field is immutable"),
]
texts = list(all_texts())
for name, pat in STALE:
    row("facts", name, [src for src, t in texts if re.search(pat, t)], 0)

nginx_unflagged = []
for src, t in texts:
    for m in re.finditer(r"\(ingress-nginx,", t):
        if "retired" not in t[m.start():m.start() + 200] and "פרש" not in t[m.start():m.start() + 200] and "הופסק" not in t[m.start():m.start() + 200]:
            nginx_unflagged.append(src)
row("facts", "#18 ingress-nginx offered as an example controller without its retirement", nginx_unflagged, 0)

hyg_abbr = [src for src, t in texts if 'ע"י' in t or "ע״י" in t]
row("hygiene", "#21 Hebrew abbreviation ע\"י instead of על ידי", hyg_abbr, 0)
dbl = [f"q{i}" for i, q in enumerate(QS) for y in q["y"] + [q["x"]] if "  " in y]
row("hygiene", "#21 double spaces in bank explanations", dbl, 0)

# ---------------- interview ----------------
row("interview", "#22 trap under 80 chars", [it["id"] for it in IV if len(it.get("w", "")) < 80], 0)
row("interview", "#23 answer point under 40 chars", [(it["id"], p) for it in IV for p in it["p"] if len(p) < 40], 0)
row("interview", "#24 follow-up doesn't end with ?", [it["id"] for it in IV if not it.get("f", "").strip().endswith("?")], 0)

# ---------------- briefing glossary ----------------
cx = re.search(r"const CODEX=\{(.*?)\n\};", HTML, re.S)
keys = sorted(re.findall(r"^'([^']+)'\s*:", cx.group(1), re.M), key=len, reverse=True) if cx else []


def norm(s):        # the page's codexNorm: no backticks, '-' and '/' read as spaces
    return re.sub(r"[-/]", " ", s.lower().replace("`", ""))


RX = {k: re.compile(r"(?<![a-z0-9_.])" + re.escape(norm(k)) + r"(?:e?s)?(?![a-z0-9_])") for k in keys}


def concepts(q):      # the page's conceptsFor: whole words, plural s/es allowed
    hay = norm(q["q"] + " " + " ".join(t for L, t in q["o"] if L in q["a"]))
    found = []
    for k in keys:
        if len(found) >= 5:
            break
        if RX[k].search(hay) and not any(k in f or f in k for f in found):
            found.append(k)
    return found


no_concept = [i for i, q in enumerate(QS[:650]) if not concepts(q)]
row("briefing", "#25 Junior-Mid questions whose briefing finds no glossary term", no_concept, 65)
row("briefing", "#26 concept matching is substring-based (indexOf) in conceptsFor",
    ["conceptsFor"] if re.search(r"function conceptsFor\(q\)\{[^}]*hay\.indexOf\(k\)", HTML) else [], 0)
row("briefing", "#27 English placeholder card in the briefing",
    ["placeholder"] if "This one is reasoning rather than a single term" in HTML else [], 0)
row("presentation", "#28 doc link labelled only 'Documentation'",
    ["authoredExplain"] if "\\u{1f4c4} Documentation</a>" in HTML else [], 0)

# ---------------- Learn ----------------
bank_stems = {re.sub(r"\W+", "", q["q"].lower()) for q in QS}
lc = collections.Counter()
per_subject_over, throwaway, three, notes_short, copies, untaught = [], [], [], [], [], []
for fname, s in BL.load():
    rec = BL.normalize(s)
    qs = [q for m in rec["modules"] for q in m["checks"]] + rec["final"]
    longest = shortest = 0
    for q in qs:
        lens = [len(o["t"]) for o in q["o"]]
        r = q["a"][0]
        lc["questions"] += 1
        if lens[r] == max(lens) and lens.count(max(lens)) == 1:
            longest += 1
        if lens[r] == min(lens) and lens.count(min(lens)) == 1:
            shortest += 1
        throwaway += [(fname, o["t"]) for k, o in enumerate(q["o"]) if k != r and len(o["t"]) < 0.55 * lens[r]]
        if len(q["o"]) != 4:
            three.append((fname, q["q"][:50]))
        notes_short += [(fname, q["q"][:40]) for o in q["o"] if len(o.get("w", "").strip()) < 60]
        if re.sub(r"\W+", "", q["q"].lower()) in bank_stems:
            copies.append((fname, q["q"][:50]))
    if longest > 0.4 * len(qs) or shortest > 0.4 * len(qs):
        per_subject_over.append((fname, f"longest {longest}/{len(qs)}", f"shortest {shortest}/{len(qs)}"))
    bodies = {m["id"]: " ".join(BL.text_of(b) for b in m["blocks"]) for m in rec["modules"]}
    for q in rec["final"]:
        asked = BL.terms(q["q"] + " " + " ".join(q["o"][a]["t"] for a in q["a"]))
        if len(asked) > 1:
            have, want = BL.stems(BL.terms(bodies[q["m"]], strip_lead=False)), BL.stems(asked)
            if len(want & have) / len(want) < 0.5:
                untaught.append((fname, q["q"][:50]))
row("learn", "#1/#2 subjects where the right option is longest or shortest in > 40% of questions", per_subject_over, 0)
row("learn", "#3 throwaway distractors (< 55% of the right option's length)", throwaway, 0)
row("learn", "#4 questions without exactly 4 options", three, 0)
row("learn", "#5/#6 options whose note is under 60 chars", notes_short, 0)
row("learn", "#7 Learn questions copied from a bank stem", copies, 0)
row("learn", "#8 final questions testing terms their part doesn't teach", untaught, 0)
asks_open = []
for fname, s in BL.load():
    for m in s["modules"]:
        for b in m["blocks"]:
            if b.get("t") == "list" and str(b.get("cap", "")).startswith("שאלות שחוזרות"):
                asks_open += [(fname, x[:40]) for x in b["x"]]
row("learn", "#30 interview questions in Learn with no answer outline", asks_open, 0)

# ---------------- Study ----------------
st_long, st_notes, st_asks = [], [], []
for f in sorted(os.listdir(os.path.join(ROOT, "study_src"))):
    if not f.endswith(".py"):
        continue
    spec = importlib.util.spec_from_file_location("c", os.path.join(ROOT, "study_src", f))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    quiz = m.CHAPTER["quiz"]
    n_long = 0
    for q in quiz:
        opts = [o["t"] if isinstance(o, dict) else o for o in q["o"]]
        lens = [len(o) for o in opts]
        if lens[0] == max(lens) and lens.count(max(lens)) == 1:
            n_long += 1
        st_notes += [(f, q["q"][:40]) for o in q["o"] if not (isinstance(o, dict) and len(o.get("w", "")) >= 60)]
    if n_long > 0.4 * len(quiz):
        st_long.append((f, f"{n_long}/{len(quiz)}"))
    for t in m.CHAPTER["topics"]:
        for b in t["blocks"]:
            if b.get("t") == "list" and str(b.get("cap", "")).startswith("שאלות שחוזרות"):
                st_asks += [(f, x[:40]) for x in b["x"]]
row("study", "#9 chapters where the right quiz option is longest in > 40%", st_long, 0)
row("study", "#10 quiz options without a note of 60+ chars", st_notes, 0)
row("study", "#30 interview questions in Study with no answer outline", st_asks, 0)

# ---------------- report ----------------
bad = 0
w = max(len(r[1]) for r in rows)
for area, item, n, limit, ex in rows:
    ok = n <= limit
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} {area:<12} {item:<{w}} {n:>5} (max {limit})" + ("" if ok else f"   e.g. {ex}"))
print(f"\n{len(rows) - bad}/{len(rows)} lines within limits")
if "--strict" in sys.argv and bad:
    sys.exit(1)
