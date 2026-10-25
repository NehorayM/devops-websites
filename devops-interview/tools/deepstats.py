#!/usr/bin/env python3
"""deepstats.py <learn_src/sNN.py ...>: per module, body length and the shortest option note, to see how deep a subject is."""
import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "learn_src"))
from build_learn import text_of  # noqa: E402
for f in sys.argv[1:]:
    spec = importlib.util.spec_from_file_location("s", f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    S = m.SUBJECT
    print(f"{os.path.basename(f)}  deep={bool(S.get('deep'))}")
    for mod in S["modules"]:
        body = sum(len(" ".join([text_of(b)])) for b in mod["blocks"])
        ws = [len(o["w"]) if isinstance(o, dict) else 0 for q in mod["checks"] for o in q["o"]]
        print(f"  {mod['id']:<22} body {body:>5}   check notes min {min(ws):>3}")
    fw = [len(o["w"]) for q in S["final"] for o in q["o"]]
    print(f"  final notes min {min(fw)}  avg {sum(fw)//len(fw)}")
