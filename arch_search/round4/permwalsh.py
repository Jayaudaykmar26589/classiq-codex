import numpy as np, sys
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import logo_pixel
F=np.array([[logo_pixel(x,y) for y in range(64)] for x in range(64)],dtype=np.float64)
H=np.array([[(-1)**bin(i&j).count('1') for j in range(64)] for i in range(64)],dtype=np.float64)
def spec(G):
    S=1-2*G; return H@S@H/4096.0
def supp(G): s=spec(G); return int((np.abs(s)>1e-9).sum())-int(abs(s[0,0])>1e-9)
def l1(G): return np.abs(spec(G)).sum()
print('identity support',supp(F),'l1',l1(F))
rng=np.random.default_rng(int(sys.argv[1]) if len(sys.argv)>1 else 0)
px=np.arange(64); py=np.arange(64)
cur=l1(F); best=(supp(F),px.copy(),py.copy())
T0,T1,N=0.5,0.002,int(sys.argv[2]) if len(sys.argv)>2 else 60000
for it in range(N):
    T=T0*(T1/T0)**(it/N)
    if rng.random()<0.5:
        i,j=rng.integers(64,size=2); px[[i,j]]=px[[j,i]]; G=F[px][:,py]
        c=l1(G)
        if c<=cur or rng.random()<np.exp((cur-c)/T): cur=c
        else: px[[i,j]]=px[[j,i]]
    else:
        i,j=rng.integers(64,size=2); py[[i,j]]=py[[j,i]]; G=F[px][:,py]
        c=l1(G)
        if c<=cur or rng.random()<np.exp((cur-c)/T): cur=c
        else: py[[i,j]]=py[[j,i]]
    if it%5000==0:
        s=supp(F[px][:,py]); print(it,round(cur,2),s,flush=True)
        if s<best[0]: best=(s,px.copy(),py.copy())
s=supp(F[px][:,py]); print('final l1',cur,'support',s)
if s<best[0]: best=(s,px.copy(),py.copy())
np.save('perm_best_%s.npy'%(sys.argv[1] if len(sys.argv)>1 else '0'),np.stack([best[1],best[2]]))
print('best support',best[0])
