# partcheck.py part.json [...]: check draft JSON parts before merge_apply (lengths, longest/shortest, why >= 72, tip >= 82)
import json,sys
L=lambda s: len(s)
tot=lg=sh=0
for p in sys.argv[1:]:
  for d in json.load(open(p,encoding='utf-8')):
    i=d['i']; r=d['r'][0]; ws=[w[0] for w in d['w']]
    lens=[L(r)]+[L(w) for w in ws]; tot+=1
    msgs=[]
    if lens[0]>1.15*max(lens[1:]): msgs.append('right too long %s'%lens)
    if min(lens[1:])<0.55*lens[0]: msgs.append('distractor too short %s'%lens)
    if lens[0]>max(lens[1:]): lg+=1; msgs.append('LONGEST %s'%lens)
    if lens[0]<min(lens[1:]): sh+=1
    for k,(t,y) in enumerate([d['r']]+d['w']):
      if L(y)<72: msgs.append('why%d %d'%(k,L(y)))
    if L(d['tip'])<82: msgs.append('tip %d'%L(d['tip']))
    if msgs: print(i,'; '.join(msgs))
print('total',tot,'longest',lg,'%d%%'%(100*lg//max(tot,1)),'shortest',sh)
