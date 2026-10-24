#!/usr/bin/env python3
"""Put isrc/interview.json into index.html as the #ivdata blob (interview mode)."""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "isrc" / "interview.json"
PAGE = HERE / "index.html"


def main():
    doc = json.loads(SRC.read_text(encoding="utf-8"))
    ids = set()
    for i, it in enumerate(doc["items"]):
        assert set(it) == {"id", "t", "s", "lv", "k", "q", "p", "f", "w", "r"}, f"item {i} has odd fields"
        assert 0 <= it["t"] < len(doc["topics"]), f"item {i} topic out of range"
        assert it["id"] not in ids, f"item {i} repeats an id"
        ids.add(it["id"])
    blob = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    s = PAGE.read_text(encoding="utf-8")
    pat = re.compile(r'(<script id="ivdata" type="application/json">).*?(</script>)', re.S)
    if pat.search(s):
        s = pat.sub(lambda m: m.group(1) + blob + m.group(2), s, count=1)
    else:
        anchor = '<script id="data" type="application/json">'
        assert anchor in s, "#data block not found"
        s = s.replace(anchor, '<script id="ivdata" type="application/json">' + blob + '</script>\n' + anchor, 1)
    PAGE.write_text(s, encoding="utf-8")
    print(f"injected {len(doc['items'])} open questions, page is {len(s) / 1e6:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
