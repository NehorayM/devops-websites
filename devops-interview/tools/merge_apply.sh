#!/bin/sh
# merge_apply.sh <name> <json parts...>: merge part files, check every question is covered, write, mark HARD, validate
set -e
name=$1; shift
python3 - "$name" "$@" <<'PY'
import json,sys,subprocess
name=sys.argv[1]; parts=sys.argv[2:]
a=[d for p in parts for d in json.load(open(p,encoding='utf-8'))]
n=len(json.loads(subprocess.check_output([sys.executable,'tools/qtool.py','dump',name])))
got=sorted(d['i'] for d in a)
assert got==list(range(n)), ('coverage', n, sorted(set(range(n))-set(got)), [i for i in got if got.count(i)>1])
json.dump(a,open('/tmp/qmerged.json','w'),ensure_ascii=False)
PY
python3 tools/qtool.py write "$name" /tmp/qmerged.json
grep -q '^HARD = True' "qsrc/$name" || sed -i '0,/^S = /s//HARD = True\nS = /' "qsrc/$name"
python3 build_bank.py 2>&1 | grep -E "problem|$name|wrote" | head -40
python3 tools/qtool.py stats "$name" | head -1
