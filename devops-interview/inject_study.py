#!/usr/bin/env python3
"""Add the Study mode to index.html: screens, styles and engine.

Sources: study_styles.css, study_screens.html, study_engine.js.

Study mode is the reference half of the app. Learn mode gates you part by part;
Study mode just lets you read. One chapter is one page: every topic in it, the
authored tables and diagrams inline, a jump bar at the top, and a handful of
multiple-choice checks at the bottom to prove the page went in.

It reuses the Learn mode's block renderer (`blocksHTML`), so both modes speak
one visual language and there is only one renderer to maintain.

Idempotent: re-running replaces the STUDY blocks rather than duplicating them.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE / "index.html"

# The sources are real files, so they can be edited and diffed like the Learn mode's.
# They were extracted from what index.html actually ran; edit them, then re-run this.
CSS = (HERE / "study_styles.css").read_text(encoding="utf-8")
SCREENS = (HERE / "study_screens.html").read_text(encoding="utf-8")
JS = (HERE / "study_engine.js").read_text(encoding="utf-8")


def block(tag, body, comment="  "):
    return f"<!-- STUDY:{tag}:BEGIN -->\n{body.strip()}\n<!-- STUDY:{tag}:END -->\n"


def put(s, tag, body, anchor, css=False, js=False):
    open_, close = f"STUDY:{tag}:BEGIN", f"STUDY:{tag}:END"
    if css or js:
        wrapped = f"/* {open_} */\n{body.strip()}\n/* {close} */\n"
    else:
        wrapped = f"<!-- {open_} -->\n{body.strip()}\n<!-- {close} -->\n"
    pat = re.compile(re.escape(("/* " if (css or js) else "<!-- ") + open_) + r".*?"
                     + re.escape(close + (" */" if (css or js) else " -->")) + r"\n", re.S)
    if pat.search(s):
        return pat.sub(lambda _: wrapped, s, count=1)
    assert anchor in s, f"anchor for {tag} not found"
    return s.replace(anchor, wrapped + anchor, 1)


def main():
    s = PAGE.read_text(encoding="utf-8")
    s = put(s, "CSS", CSS, "/* ---------- home ---------- */", css=True)
    s = put(s, "SCREENS", SCREENS, "  <!-- NUMBERED PRACTICE EXAMS -->")
    s = put(s, "JS", JS, "const LEARN_T={", js=True)

    # the router has to know the new screens or they never lose .hidden
    for sid in ("stuPickScreen", "stuReadScreen"):
        if f"'{sid}'" not in s.split("function go(")[0].split("const SCREENS=")[1].split("];")[0]:
            s = s.replace("'simRevScreen','simDoneScreen','paperScreen','timerScreen',",
                          "'simRevScreen','simDoneScreen','paperScreen','stuPickScreen','stuReadScreen','timerScreen',", 1)
            break

    # every id the engine touches must exist in the markup
    ids = set(re.findall(r"\$\('([A-Za-z0-9_]+)'\)", CSS + SCREENS + JS))
    have = set(re.findall(r'id="([A-Za-z0-9_]+)"', s))
    missing = sorted(i for i in ids if i not in have)
    assert not missing, f"engine touches ids that do not exist: {missing}"

    PAGE.write_text(s, encoding="utf-8")
    print(f"study mode injected · {len(ids)} element ids checked · page {len(s)/1e6:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
