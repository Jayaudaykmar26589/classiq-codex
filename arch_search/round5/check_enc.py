import sys, json, numpy as np
d=np.load('ferrers.npz'); lam=d['lam']; lev=d['lev']
side=sys.argv[1]; J=json.load(open(sys.argv[2])); nanc=J['nanc']
if side=='y': pts=range(64); init=lambda v:[(v>>b)&1 for b in range(5)]+[0]*nanc+[(v>>5)&1]; want=lambda v:int(lev[v])
else: pts=range(128); init=lambda v:[((v&63)>>b)&1 for b in range(6)]+[0]*nanc+[v>>6]; want=lambda v:int(lam[v&63,v>>6])
codes={}; seen=set()
for v in pts:
    w=init(v)
    for k,t,a,na,b,nb in J['ops']:
        if k==2: continue
        A=w[a]^na
        if k==0: w[t]^=A
        else: w[t]^=A&(w[b]^nb)
    st=tuple(w); assert st not in seen; seen.add(st)
    c=tuple(w[i] for i in J['cw']); codes.setdefault(c,set()).add(want(v))
bad=[c for c,s in codes.items() if len(s)>1]
print('injective ok; codes used',len(codes),'inconsistent codes',len(bad),{c:sorted(s) for c,s in codes.items()})
