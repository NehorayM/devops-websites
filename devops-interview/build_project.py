#!/usr/bin/env python3
"""Build the "my project" question set and put it into index.html.

The DevOps bank (qsrc/, 1,300 questions, exams 1-20) is one thing; the owner's own project is
another. Its questions live in psrc/ and reach the page as a second blob, #projdata, which the
page appends to the bank at load as one more subject with its own exams (21, 22, ...). Nothing
in the DevOps bank, its version stamp (BANKV) or the duel answer key changes when this runs.

Reads  psrc/pN.py           one exam per file: PAPER_LEN Q() calls with section "project"
Writes psrc/project.json    {"section", "short", "papers", "questions"}
       index.html           the #projdata blob, PROJV and PROJV_OK

    python3 build_project.py            # every file must hold a full exam
    python3 build_project.py --partial  # while authoring: checks everything but the counts

Questions follow the same rules as the bank (build_bank.validate, HARD rules included): four
options, the right one first, a Hebrew note per option, a Hebrew tip, a doc link. An exam's
questions are shuffled inside their own file's slots, so adding exam N+1 never moves exam N.
"""
import hashlib
import importlib.util
import json
import pathlib
import random
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
PSRC = HERE / "psrc"
OUT = PSRC / "project.json"
SLOTS = PSRC / "projv.json"
PAGE = HERE / "index.html"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "qsrc"))
import build_bank as bb  # noqa: E402
from qlib import SECTIONS, T  # noqa: E402

SLUG = "project"
NAME = "My project: weather-app on EKS"
SHORT = "My project"
SEC = len(SECTIONS)             # the page appends it after the bank's own subjects
SEED = 20261112
LETTERS = "ABCD"

# The site is public and the project is real, so its identifiers stay out of everything that is
# published about it: account numbers, resource ids, public addresses, the domain, mail addresses
# and anything shaped like a key. Private, loopback, link-local and documentation ranges are fine.
import ipaddress  # noqa: E402

LEAKS = [
    (re.compile(r"(?<![\w.])\d{12}(?![\w.])"), "a 12-digit number (an AWS account id?)"),
    (re.compile(r"\b(?:i|ami|vol|snap|sg|vpc|subnet|eni|nat|igw|rtb|acl)-[0-9a-f]{8,17}\b"), "an AWS resource id"),
    (re.compile(r"\barn:aws[\w-]*:[^\s`\"']*\d{12}"), "an ARN with an account id"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I), "a mail address"),
    (re.compile(r"\b[\w-]+\.click\b", re.I), "the project's domain"),
    (re.compile(r"\b(?:glpat-|ghp_|sb_secret_|AKIA|ASIA)[A-Za-z0-9_-]{8,}"), "a credential with a known prefix"),
    (re.compile(r"\b[0-9a-f]{32,}\b"), "a long hex string (a key or a hash?)"),
]
# A random key mixes cases and digits; a long identifier (enable_cluster_creator_admin_permissions) doesn't.
TOKEN = re.compile(r"(?<![\w+/-])[A-Za-z0-9+/_-]{32,}(?![\w+/-])")
IPV4 = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?:/\d{1,2})?(?![\w.])")
DOC_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]


def leaks(text):
    """What in this text must not be published, as a list of (found, why)."""
    out = [(m.group(0), why) for rx, why in LEAKS for m in rx.finditer(text)]
    for m in TOKEN.finditer(text):
        t = m.group(0)
        if re.search(r"[a-z]", t) and re.search(r"[A-Z]", t) and len(re.findall(r"\d", t)) >= 3:
            out.append((t, "a long token-like string"))
    for m in IPV4.finditer(text):
        try:
            ip = ipaddress.ip_address(m.group(1))
        except ValueError:
            continue
        if not (ip.is_private or ip.is_loopback or ip.is_link_local or any(ip in n for n in DOC_NETS)):
            out.append((m.group(0), "a public IP address"))
    return out


def load():
    files = sorted(PSRC.glob("p[0-9]*.py"), key=lambda f: int(re.sub(r"\D", "", f.stem)))
    papers = []
    for k, f in enumerate(files, 1):
        if f.stem != f"p{k}":
            sys.exit(f"{f.name}: exam files must be p1.py, p2.py, ... with no gaps")
        spec = importlib.util.spec_from_file_location("psrc_" + f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        got = getattr(mod, "QS", None)
        if not isinstance(got, list):
            sys.exit(f"{f.name}: defines no QS list")
        if not getattr(mod, "HARD", False):
            sys.exit(f"{f.name}: project exams are HARD = True files")
        bb.HARD_FILES.add(f.name)
        papers.append((f.name, got))
    return papers


def validate(papers, partial):
    bb.SEC_INDEX[SLUG] = SEC
    qs = [q for _f, got in papers for q in got]
    errs, _report = bb.validate(qs, True)
    bank = json.loads(bb.OUT.read_text(encoding="utf-8"))["questions"]
    core = {bb.norm(q["q"]) for q in bank}
    for q in qs:
        text = " ".join([q.q, q.tip] + [x for o in q.opts for x in o])
        for found, why in leaks(text):
            errs.append(f"{q.src}: {found!r} looks like {why}; the site is public, leave it out")
        if q.sec != SLUG:
            errs.append(f"{q.src}: a project question must use section {SLUG!r}")
        if bb.norm(q.q) in core:
            errs.append(f"{q.src}: this stem is already a question in the DevOps bank")
    if len(bank) % bb.PAPER_LEN:
        errs.append(f"the DevOps bank has {len(bank)} questions: project exams need it to end on a full paper")
    for fname, got in papers:
        n, t = len(got), sum(1 for q in got if q.kind == T)
        if not partial and n != bb.PAPER_LEN:
            errs.append(f"{fname}: {n} questions, an exam is {bb.PAPER_LEN}")
        if n > bb.PAPER_LEN:
            errs.append(f"{fname}: {n} questions, an exam is at most {bb.PAPER_LEN}")
        if n >= 20 and not 0.35 * n <= t <= 0.65 * n:
            errs.append(f"{fname}: {t} troubleshooting of {n} - keep it between 35% and 65%")
    return errs


def compose(papers):
    out = []
    for k, (_fname, got) in enumerate(papers, 1):
        rng = random.Random(SEED + 1000 * k)
        order = list(got)
        rng.shuffle(order)
        slots = [i % 4 for i in range(len(order))]
        rng.shuffle(slots)
        for q, pos in zip(order, slots):
            wrong = q.opts[1:]
            rng.shuffle(wrong)
            opts = wrong[:pos] + [q.opts[0]] + wrong[pos:]
            out.append({
                "s": SEC, "q": q.q.strip(),
                "o": [[LETTERS[i], o[0].strip()] for i, o in enumerate(opts)],
                "a": [LETTERS[pos]],
                "y": [o[1].strip() for o in opts],
                "x": q.tip.strip(), "lv": q.lv, "k": q.kind, "r": q.ref,
            })
    return out


def stamp(qs):
    """A version for the project slots, with the earlier versions that still fit them.

    Like BANKV: a slot is its stem. Earlier stamps stay valid while every slot they knew
    still holds the same question (95% in place), so adding an exam or rewording an option
    keeps what the learner has seen, got wrong and bookmarked there.
    """
    stems = [hashlib.sha1(re.sub(r"\W+", "", q["q"].lower()).encode("utf-8")).hexdigest()[:12] for q in qs]
    ver = "p" + hashlib.sha1("".join(stems).encode("utf-8")).hexdigest()[:9]
    prev = json.loads(SLOTS.read_text(encoding="utf-8")) if SLOTS.exists() else None
    if prev is None:
        compat = []
    elif prev["ver"] == ver:
        compat = prev["compat"]
    else:
        old = prev["stems"]
        same = len(stems) >= len(old) and sum(a == b for a, b in zip(old, stems)) >= 0.95 * len(old)
        compat = (prev["compat"] + [prev["ver"]])[-20:] if same else []
        print(("project: slots kept, earlier versions stay valid" if same else
               "project: slots changed, progress on project questions will reset") + f" ({prev['ver']} -> {ver})")
    compat = [c for c in dict.fromkeys(compat) if c != ver]
    SLOTS.write_text(json.dumps({"ver": ver, "compat": compat, "stems": stems}), encoding="utf-8")
    return ver, compat


def inject(doc, ver, compat):
    s = PAGE.read_text(encoding="utf-8")
    blob = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    pat = re.compile(r'(<script id="projdata" type="application/json">).*?(</script>)', re.S)
    if pat.search(s):
        s = pat.sub(lambda m: m.group(1) + blob + m.group(2), s, count=1)
    else:
        anchor = '<script id="data" type="application/json">'
        assert anchor in s, "#data block not found"
        s = s.replace(anchor, '<script id="projdata" type="application/json">' + blob + '</script>\n' + anchor, 1)
    assert "const PROJV='" in s and "const PROJV_OK=[" in s, "PROJV constants not found in the page"
    s = re.sub(r"const PROJV='[^']*';", "const PROJV='%s';" % ver, s, count=1)
    s = re.sub(r"const PROJV_OK=\[[^\]]*\];", "const PROJV_OK=%s;" % json.dumps(compat), s, count=1)
    PAGE.write_text(s, encoding="utf-8")
    return len(s)


def main():
    partial = "--partial" in sys.argv
    papers = load()
    errs = validate(papers, partial)
    n = sum(len(g) for _f, g in papers)
    print(f"{n} project questions in {len(papers)} exam file(s)")
    if errs:
        print(f"\n{len(errs)} problem(s):")
        for e in errs[:80]:
            print("  " + e)
        sys.exit(1)
    qs = compose(papers)
    for fname, got in papers:
        lg = sum(1 for q in got if len(q.opts[0][0]) > max(len(o[0]) for o in q.opts[1:]))
        sh = sum(1 for q in got if len(q.opts[0][0]) < min(len(o[0]) for o in q.opts[1:]))
        t = sum(1 for q in got if q.kind == T)
        print(f"  {fname}: {len(got)} questions, {t} troubleshooting, right option longest {lg} / shortest {sh}")
    doc = {"v": 1, "section": NAME, "short": SHORT, "papers": len(papers), "questions": qs}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=0), encoding="utf-8")
    ver, compat = stamp(qs)
    size = inject(doc, ver, compat)
    print(f"injected {len(qs)} project questions (stamp {ver}), page is {size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
