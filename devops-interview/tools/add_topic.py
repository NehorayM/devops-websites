#!/usr/bin/env python3
"""add_topic.py <study_src/cN_x.py> <snippet.py>: append Study topic pages and quiz checks to a chapter.

The snippet holds Python source: one or more topic dicts ({"nm": ..., "blocks": [...]},), then a line
`#---QUIZ---`, then zero or more `QZ(...)` calls. Topics go to the end of the chapter's topic list,
checks to the end of its quiz. Refuses to add a topic whose name already exists. Run build_study.py after.
"""
import re, sys
path, snip = sys.argv[1], sys.argv[2]
src = open(path, encoding="utf-8").read()
top, quiz = (open(snip, encoding="utf-8").read().split("#---QUIZ---") + [""])[:2]
for nm in re.findall(r'\{"nm": "([^"]+)"', top):
    if f'{{"nm": "{nm}"' in src:
        sys.exit(f"{path}: topic {nm!r} already exists")
a = '\n ],\n "quiz": ['
assert src.count(a) == 1, "topics end not found"
src = src.replace(a, "\n  " + top.strip().rstrip(",") + "," + a, 1)
if quiz.strip():
    end = src.rindex("\n ],\n}")
    src = src[:end] + "\n  " + quiz.strip().rstrip(",") + "," + src[end:]
open(path, "w", encoding="utf-8").write(src)
print(f"{path}: added {len(re.findall(chr(123)+'\"nm\"', top))} topic(s), {quiz.count('QZ(')} check(s)")
