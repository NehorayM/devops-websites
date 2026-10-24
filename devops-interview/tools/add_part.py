#!/usr/bin/env python3
"""add_part.py <learn_src/sNN_x.py> <snippet.py>: add one Learn module and swap in one final question.

The snippet holds Python source: a `MOD(...)` call, a line `#---FINAL---`, then one `F(...)` call
whose m= is the new module's id. The module is appended to the subject's module list, and the new
final replaces the last question of the final exam (the exam must stay at exactly 10 and touch every
module). Refuses to run twice for the same module id. Run build_learn.py afterwards to validate.
"""
import re, sys
path, snip = sys.argv[1], sys.argv[2]
src = open(path, encoding="utf-8").read()
mod_src, fin_src = open(snip, encoding="utf-8").read().split("#---FINAL---")
mid = re.search(r'MOD\(\s*"([^"]+)"', mod_src).group(1)
if re.search(r'MOD\(\s*"%s"' % re.escape(mid), src):
    sys.exit(f"{path}: module {mid!r} already exists")
anchor = '\n ],\n\n "recap"'
assert src.count(anchor) == 1, "modules list end not found"
src = src.replace(anchor, "\n\n  " + mod_src.strip() + ",\n" + anchor, 1)
end = '\n ],\n}'
assert src.rstrip().endswith(end.strip()) or src.count(end) == 1, "final list end not found"
i_end = src.rindex(end)
i_last = src.rindex("\n   F(", 0, i_end)
src = src[:i_last] + "\n   " + fin_src.strip().rstrip(",") + "," + src[i_end:]
open(path, "w", encoding="utf-8").write(src)
print(f"{path}: added module {mid!r} and replaced the last final question")
