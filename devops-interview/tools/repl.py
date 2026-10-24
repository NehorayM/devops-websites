# repl.py file.py fixes.json: fixes.json is [[old_text, new_text], ...]; each old text must occur exactly once
import json,sys,pathlib
p=pathlib.Path('qsrc')/sys.argv[1]; s=p.read_text(encoding='utf-8')
for old,new in json.load(open(sys.argv[2],encoding='utf-8')):
    o=json.dumps(old,ensure_ascii=False); n=json.dumps(new,ensure_ascii=False)
    assert s.count(o)==1,(s.count(o),old)
    s=s.replace(o,n)
p.write_text(s,encoding='utf-8'); print('replaced',len(json.load(open(sys.argv[2],encoding='utf-8'))))
