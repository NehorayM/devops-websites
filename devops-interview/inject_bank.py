#!/usr/bin/env python3
"""Put qsrc/bank.json into index.html as the #data blob.

The old bank's question indices are stored in the profile (seen, wrong,
bookmarks, spaced repetition), so the bank carries a version stamp and the
page clears anything index-keyed when that stamp changes.
"""
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
BANK = HERE / "qsrc" / "bank.json"
PAGE = HERE / "index.html"
SLOTS = HERE / "qsrc" / "bankv.json"     # what the last build's slots held, to tell a reword from a reshuffle

RESET = """  // the question bank is index-keyed; a new bank invalidates anything that
  // stored an index, so those fields start over while progress is kept
  if(P.bank!==BANKV&&!BANKV_OK.includes(P.bank)){
    P.bank=BANKV; P.seen={}; P.wrong=[]; P.marks=[]; P.sr={};
  }
  P.bank=BANKV;
"""


def main():
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    qs = bank["questions"]
    n = len(bank["sections"])
    assert len(bank["short"]) == n, "every section needs a short name"
    seen = set()
    for i, q in enumerate(qs):
        assert set(q) <= {"s", "q", "o", "a", "y", "x", "lv", "k", "r"}, f"q{i} has odd fields {set(q)}"
        assert {"s", "q", "o", "a", "y", "x", "lv", "k"} <= set(q), f"q{i} is missing a field"
        assert 0 <= q["s"] < n, f"q{i} section out of range"
        assert q["a"] and all(a in {l for l, _ in q["o"]} for a in q["a"]), f"q{i} bad answer"
        assert len(q["o"]) == len(q["y"]) == 4, f"q{i} needs four options, each explained"
        k = re.sub(r"\W+", "", q["q"].lower())[:400]
        assert k not in seen, f"q{i} duplicates an earlier question"
        seen.add(k)

    blob = json.dumps(bank, ensure_ascii=False, separators=(",", ":"))
    # The stamp exists to detect "index 412 now points at a different question". A slot's
    # meaning is its sector and its stem: rewording an option or an explanation must not
    # throw away anyone's progress, and neither should a stem edit that keeps the question.
    stems = [hashlib.sha1((str(q["s"]) + "|" + re.sub(r"\W+", "", q["q"].lower())).encode("utf-8")).hexdigest()[:12]
             for q in qs]
    ver = hashlib.sha1("".join(stems).encode("utf-8")).hexdigest()[:10]
    # Versions whose slots hold the same questions stay valid: same length, same sector in
    # every slot, and at least 95% of the stems unchanged in place. An insert, delete or
    # reorder shifts most slots and fails this, so it still resets as it should.
    s_page = PAGE.read_text(encoding="utf-8")
    prev = json.loads(SLOTS.read_text(encoding="utf-8")) if SLOTS.exists() else None
    if prev is None:
        # first build with slot tracking: the bank on the page is this same bank in the
        # same order (only option text changed since), so its stamp carries over
        m = re.search(r"const BANKV='([^']*)';", s_page)
        compat = [m.group(1)] if m else []
    elif prev["ver"] == ver:
        compat = prev["compat"]
    else:
        same = (len(prev["stems"]) == len(stems)
                and prev.get("secs") == [q["s"] for q in qs]
                and sum(a == b for a, b in zip(prev["stems"], stems)) >= 0.95 * len(stems))
        compat = (prev["compat"] + [prev["ver"]])[-20:] if same else []
        print(("bank: slots kept, earlier versions stay valid" if same else
               "bank: slots changed, progress will reset") + f" ({prev['ver']} -> {ver})")
    compat = [c for c in dict.fromkeys(compat) if c != ver]
    SLOTS.write_text(json.dumps({"ver": ver, "compat": compat, "secs": [q["s"] for q in qs], "stems": stems}),
                     encoding="utf-8")

    s = s_page
    pat = re.compile(r'(<script id="data" type="application/json">).*?(</script>)', re.S)
    assert pat.search(s), "#data block not found"
    # only "</" needs neutralising inside a <script> block; "\/" is a legal JSON escape
    s = pat.sub(lambda m: m.group(1) + blob.replace("</", "<\\/") + m.group(2), s, count=1)

    # the version constant
    ok = "const BANKV_OK=%s;" % json.dumps(compat)
    if "const BANKV=" in s:
        s = re.sub(r"const BANKV='[^']*';", "const BANKV='%s';" % ver, s, count=1)
        if "const BANKV_OK=" in s:
            s = re.sub(r"const BANKV_OK=\[[^\]]*\];", ok, s, count=1)
        else:
            s = s.replace("const BANKV='%s';" % ver, "const BANKV='%s';\n%s" % (ver, ok), 1)
    else:
        anchor = "const QS=DATA.questions, SECTIONS=DATA.sections, SHORT=DATA.short||SECTIONS;"
        assert anchor in s, "bank loading line not found"
        s = s.replace(anchor, anchor + "\nconst BANKV='%s';" % ver, 1)

    # the reset, inside loadProfile right after the stored profile is merged in
    if "BANKV_OK.includes(P.bank)" not in s:
        anchor = "    if(r) Object.assign(P,JSON.parse(r.value));\n  }catch(e){}\n"
        assert anchor in s, "loadProfile anchor not found"
        s = s.replace(anchor, anchor + RESET, 1)

    PAGE.write_text(s, encoding="utf-8")
    print(f"injected {len(qs)} questions (bank {ver}), page is {len(s) / 1e6:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
