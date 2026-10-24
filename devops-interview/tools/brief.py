import json,sys,subprocess
d=json.loads(subprocess.check_output([sys.executable,__file__.replace('brief.py','qtool.py'),'dump',sys.argv[1]]))
for q in d:
    print(f"#{q['i']} [{q['lv']},{q['kind']}] {q['q']}\n  R: {q['r'][0]}")
    for w in q['w']: print('  W:',w[0])
