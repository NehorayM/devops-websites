# list stub why-lines on wrong options: file, line of the why string, stem, right, option, why
import ast,sys,pathlib,json
out=[]
for f in sorted(pathlib.Path('qsrc').glob('*.py')):
    if f.name=='qlib.py': continue
    t=ast.parse(f.read_text(encoding='utf-8'))
    for n in ast.walk(t):
        if isinstance(n,ast.Call) and getattr(n.func,'id','')=='Q':
            a=n.args; stem=ast.literal_eval(a[3]); right=ast.literal_eval(a[4])
            for w in a[5:]:
                txt,why=ast.literal_eval(w)
                if len(why)<15: out.append(dict(f=f.name,line=w.elts[1].lineno,col=w.elts[1].col_offset,stem=stem,right=right[0],opt=txt,why=why))
if len(sys.argv)>1: out=[o for o in out if o['f']==sys.argv[1]]
json.dump(out,sys.stdout,ensure_ascii=False)
