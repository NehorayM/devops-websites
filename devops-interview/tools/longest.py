# longest.py file.py: questions whose right option is the longest, with lengths (to rebalance)
import json,sys,subprocess
d=json.loads(subprocess.check_output([sys.executable,__file__.replace('longest.py','qtool.py'),'dump',sys.argv[1]]))
for q in d:
    L=[len(q['r'][0])]+[len(w[0]) for w in q['w']]
    if L[0]>max(L[1:]):
        print(f"#{q['i']} {L}  R: {q['r'][0]}")
        for w in q['w']: print(f"     W({len(w[0])}): {w[0]}")
