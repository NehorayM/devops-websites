# short.py file.py [min]: explanations or tips below the HARD minimum, for fixing with tools/repl.py
import json,sys,subprocess
d=json.loads(subprocess.check_output([sys.executable,__file__.replace('short.py','qtool.py'),'dump',sys.argv[1]]))
m=int(sys.argv[2]) if len(sys.argv)>2 else 70
for q in d:
    for t,w in [q['r']]+q['w']:
        if len(w)<m: print(json.dumps({"opt":t,"why":w},ensure_ascii=False))
    if len(q['tip'])<80: print(json.dumps({"tip":q['tip']},ensure_ascii=False))
