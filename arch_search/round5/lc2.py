"""Level-code SA with a fixed code->level map; moves keep level validity; per-half capacity penalty."""
import sys, numpy as np
d=np.load('ferrers.npz'); lam=d['lam']; lev=d['lev']
side=sys.argv[1]; CAP=int(sys.argv[2]); seed=int(sys.argv[3]); NIT=int(sys.argv[4]); Lmap=[int(v) for v in sys.argv[5].split(',')]
if side=='x': n=7; want=np.array([lam[i&63,i>>6] for i in range(128)]); half=np.array([i>>6 for i in range(128)])
else: n=6; want=np.array([lev[i] for i in range(64)]); half=np.array([i>>5 for i in range(64)])
N=1<<n; POP=np.array([bin(j).count('1') for j in range(N)]); L=np.array(Lmap)
def mob(a):
    a=a.copy()
    for i in range(n):
        s=1<<i; a=a.reshape(-1,2*s); a[:,s:]^=a[:,:s]; a=a.reshape(-1)
    return a
def degs(c): return [int(POP[mob(((c>>b)&1).astype(np.uint8)).astype(bool)].max(initial=0)) for b in range(3)]
def over(c): return sum(max(0,int(((c==k)&(half==h)).sum())-CAP) for k in range(8) for h in (0,1))
def cost(c): dg=degs(c); return 50*over(c)+sum(max(0,x-2)**2 for x in dg), dg
rng=np.random.default_rng(seed)
opts=[np.nonzero(L==want[i])[0] for i in range(N)]
assert all(len(o) for o in opts), 'map lacks a level'
best=None
for rs in range(3):
    c=np.array([rng.choice(o) for o in opts]); cur,dg=cost(c)
    for it in range(NIT):
        T=10*(0.02/10)**(it/NIT); c2=c.copy()
        if rng.random()<0.7: i=rng.integers(N); c2[i]=rng.choice(opts[i])
        else:
            i,j=rng.integers(N,size=2)
            if want[i]==want[j]: c2[i],c2[j]=c[j],c[i]
        n2,dg2=cost(c2)
        if n2<=cur or rng.random()<np.exp((cur-n2)/T): c,cur,dg=c2,n2,dg2
    if best is None or cur<best[0]: best=(cur,c.copy(),dg)
print(side,'cap',CAP,'map',Lmap,'seed',seed,'overflow',over(best[1]),'code-bit degrees',best[2],flush=True)
np.save(f'lc2_{side}_{CAP}_{seed}_{"".join(map(str,Lmap))}.npy',best[1])
