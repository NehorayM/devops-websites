# fitcheck.py file.py cands.json: cands = {"i": "new right text"}; prints length vs distractors and whether it lands mid-pack
import json,sys,subprocess
d={q['i']:q for q in json.loads(subprocess.check_output([sys.executable,__file__.replace('fitcheck.py','qtool.py'),'dump',sys.argv[1]]))}
c=json.load(open(sys.argv[2],encoding='utf-8')); out=[]
for i,t in c.items():
    q=d[int(i)]; W=sorted(len(w[0]) for w in q['w']); L=len(t)
    ok = W[0] <= L <= W[-1]
    print(f"#{i} {'OK ' if ok else 'BAD'} {L} vs {W}  {t}")
    if ok: out.append([q['r'][0],t])
json.dump(out,open('/tmp/fit_ok.json','w'),ensure_ascii=False)
