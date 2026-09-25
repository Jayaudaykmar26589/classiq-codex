"""Joint SA over x/y refined 5-bit codes: encoder bits degree<=4, kernel (10-bit) sparse & low degree."""
import sys, numpy as np
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import logo_pixel
M=np.array([[logo_pixel(x,y) for y in range(64)] for x in range(64)],dtype=np.uint8)
seed=int(sys.argv[1]); N_IT=int(sys.argv[2]); CAPX=int(sys.argv[3]); CAPY=int(sys.argv[4]); lam=float(sys.argv[5])
NB=5; NC=32
labx=np.unique(M,axis=0,return_inverse=True)[1].ravel(); laby=np.unique(M.T,axis=0,return_inverse=True)[1].ravel()
POP=np.array([bin(j).count('1') for j in range(1024)])
def mob(a,n):
    a=a.copy()
    for i in range(n):
        s=1<<i; a=a.reshape(-1,2*s); a[:,s:]^=a[:,:s]; a=a.reshape(-1)
    return a
def encdeg(c,lab,cap):
    v=0
    for k in np.unique(c):
        m=c==k; v+=len(set(lab[m]))-1+max(0,int(m.sum())-cap)
    ex=0
    for b in range(NB):
        a=mob(((c>>b)&1).astype(np.uint8),6); d=POP[:64][a.astype(bool)].max(initial=0); ex+=max(0,d-4)
    return v,ex
def kern(cx,cy):
    g=np.zeros((NC,NC),np.uint8); g[np.ix_(cx,cy)]=M   # unused codes -> 0
    a=mob(g.reshape(-1).copy(),10).astype(bool)          # index = cx*32+cy
    deg=POP[a]; return int(a.sum()), int((deg>3).sum()), int(deg.max(initial=0))
def cost(cx,cy):
    vx,ex=encdeg(cx,labx,CAPX); vy,ey=encdeg(cy,laby,CAPY); nt,hi,md=kern(cx,cy)
    return 1000*(vx+vy)+30*(ex+ey)+lam*hi+0.2*nt,(vx+vy,ex+ey,nt,hi,md)
rng=np.random.default_rng(seed)
def init(lab,cap):
    c=np.zeros(64,int); nxt=0
    for L in range(lab.max()+1):
        idx=np.nonzero(lab==L)[0]
        for t in range(0,len(idx),cap): c[idx[t:t+cap]]=nxt%NC; nxt+=1
    return c
cx=init(labx,CAPX); cy=init(laby,CAPY); cur,info=cost(cx,cy); best=(cur,cx.copy(),cy.copy(),info)
for it in range(N_IT):
    T=20*(0.02/20)**(it/N_IT)
    ax=rng.random()<0.5; c=(cx if ax else cy).copy()
    if rng.random()<0.5: c[rng.integers(64)]=rng.integers(NC)
    else: i,j=rng.integers(64,size=2); c[i],c[j]=c[j],c[i]
    n,inf=cost(c,cy) if ax else cost(cx,c)
    if n<=cur or rng.random()<np.exp((cur-n)/T):
        cur,info=n,inf
        if ax: cx=c
        else: cy=c
        if cur<best[0]: best=(cur,cx.copy(),cy.copy(),info)
    if it%20000==0: print(it,round(cur,1),info,flush=True)
print('BEST viol,degexcess,kernelANF,terms>deg3,maxdeg =',best[3],flush=True)
np.savez(f'joint_{seed}.npz',cx=best[1],cy=best[2])
