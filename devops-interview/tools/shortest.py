# shortest.py file.py: questions whose right option is the shortest, with lengths (to rebalance)
import json,sys,subprocess
d=json.loads(subprocess.check_output([sys.executable,__file__.replace('shortest.py','qtool.py'),'dump',sys.argv[1]]))
for q in d:
    L=[len(q['r'][0])]+[len(w[0]) for w in q['w']]
    if L[0]<min(L[1:]):
        print(f"#{q['i']} {L}  R: {q['r'][0]}")
