# patch.py part.json patches.json : patches = {"i": {"r": "new right text", "w0": "new wrong text", "y0": "new right why", "y1".."y3": new wrong whys, "tip": ...}}
import json,sys
p,q=sys.argv[1],sys.argv[2]
D=json.load(open(p,encoding='utf-8')); P=json.load(open(q,encoding='utf-8'))
by={str(d['i']):d for d in D}
for i,ch in P.items():
  d=by[i]
  for k,v in ch.items():
    if k=='r': d['r'][0]=v
    elif k=='tip': d['tip']=v
    elif k[0]=='w': d['w'][int(k[1])-1][0]=v
    elif k=='y0': d['r'][1]=v
    elif k[0]=='y': d['w'][int(k[1])-1][1]=v
json.dump(D,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
print('patched',len(P))
