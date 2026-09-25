# enumerate code->level maps up to affine equivalence (AGL(3,2)) and kernel sizes for (y-map, x-map) pairs
import numpy as np, itertools, json
def fwht(a):
    a=a.astype(float).copy(); h=1
    while h<len(a):
        a=a.reshape(-1,2*h); u=a[:,:h].copy(); v=a[:,h:].copy(); a[:,:h]=u+v; a[:,h:]=u-v; a=a.reshape(-1); h*=2
    return a
# AGL(3,2) as permutations of 0..7
mats=[]
for cols in itertools.product(range(1,8),repeat=3):
    M=np.array([[(c>>i)&1 for c in cols] for i in range(3)])
    if round(abs(np.linalg.det(M)))%2==1: mats.append(cols)
perms=set()
for cols in mats:
    for t in range(8):
        p=[]
        for v in range(8):
            w=t
            for i in range(3):
                if (v>>i)&1: w^=cols[i]
            p.append(w)
        perms.add(tuple(p))
perms=list(perms); print('AGL size',len(perms))
def classes(mult):
    seen=set(); reps=[]
    items=[l for l,m in mult for _ in range(m)]
    for arr in set(itertools.permutations(items)):
        if arr in seen: continue
        orb=set(tuple(arr[p[v]] for v in range(8)) for p in perms)
        seen|=orb; reps.append(arr)
    return reps
Y=classes([(1,1),(2,1),(3,1),(4,1),(5,2),(7,2)])
X=classes([(0,3),(1,1),(2,1),(3,1),(4,1),(5,1)])
print('y classes',len(Y),'x classes',len(X))
res=[]
for ly in Y:
    for lx in X:
        g=np.array([1 if ly[cy]<=lx[cx] else 0 for cy in range(8) for cx in range(8)])
        s=int((np.abs(fwht(1-2*g))>1e-9).sum())-1
        res.append((s,ly,lx))
res.sort()
for r in res[:25]: print(r)
json.dump([(s,list(ly),list(lx)) for s,ly,lx in res],open('maps.json','w'))
