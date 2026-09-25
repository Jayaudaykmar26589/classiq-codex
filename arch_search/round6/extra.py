"""For near-miss encoders: does (code wires + 1 or 2 extra final wires) become level-consistent?"""
import json, glob, sys, itertools, numpy as np
d=np.load('ferrers.npz'); lev=d['lev']; lam=d['lam']
side=sys.argv[1]; pat=sys.argv[2]
def finals(J):
    nanc=J['nanc']; out=[]
    if side=='y': pts=[( [(v>>b)&1 for b in range(5)]+[0]*nanc+[(v>>5)&1], int(lev[v])) for v in range(64)]
    else: pts=[( [((v&63)>>b)&1 for b in range(6)]+[0]*nanc+[v>>6], int(lam[v&63,v>>6])) for v in range(128)]
    for w,l in pts:
        w=list(w)
        for k,t,a,na,b,nb in J['ops']:
            if k==2: continue
            A=w[a]^na
            if k==0: w[t]^=A
            else: w[t]^=A&(w[b]^nb)
        out.append((w,l))
    return out
def consistent(F, wires):
    m={}
    for w,l in F:
        c=tuple(w[i] for i in wires)
        if m.setdefault(c,l)!=l: return False
    return True
for f in sorted(glob.glob(pat)):
    J=json.load(open(f)); F=finals(J); NW=len(F[0][0]); cw=J['cw']
    others=[w for w in range(NW) if w not in cw]
    ok1=[w for w in others if consistent(F, cw+[w])]
    ok2=[p for p in itertools.combinations(others,2) if consistent(F, cw+list(p))] if not ok1 else []
    # also any 4 wires at all
    any4=[q for q in itertools.combinations(range(NW),4) if consistent(F, list(q))]
    print(f.split('/')[-1], 'NW',NW,'cw',cw,'+1:',ok1,'+2:',ok2[:5],'any4:',any4[:5], flush=True)
