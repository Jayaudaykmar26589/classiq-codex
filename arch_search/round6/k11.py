# kernel size for h-independent 11-class x code (4 bits) + y level code (3 bits, per-h map) + h
import numpy as np, sys
d=np.load('ferrers.npz'); lev=d['lev']; lam=d['lam']
cls={}
for x in range(64): cls.setdefault((int(lam[x,0]),int(lam[x,1])),[]).append(x)
C=sorted(cls); print(len(C),[ (c,len(cls[c])) for c in C])
lam0=[c[0] for c in C]; lam1=[c[1] for c in C]; size=[len(cls[c]) for c in C]
def fwht(a):
    a=a.astype(float).copy(); h=1
    while h<len(a):
        a=a.reshape(-1,2*h); u=a[:,:h].copy(); v=a[:,h:].copy(); a[:,:h]=u+v; a[:,h:]=u-v; a=a.reshape(-1); h*=2
    return a
rng=np.random.default_rng(int(sys.argv[1]))
LV=[1,2,3,4,5,7]
def build(ax,ay):
    # index = cx | cy<<4 | h<<7
    g=np.zeros(256,int)
    for h in range(2):
        for cy in range(8):
            for cx in range(16):
                l=ay[h][cy]; lamv=(lam0 if h==0 else lam1)[ax[cx]]
                g[cx|(cy<<4)|(h<<7)]= 1 if l<=lamv else 0
    return g
def cost(ax,ay):
    w=fwht(1-2*build(ax,ay)); return int((np.abs(w)>1e-9).sum())-1
def feasible(ax,ay,nx=1,ny=1):
    capx=1<<(6+nx-4)
    for k in range(11):
        if ax.count(k)*capx<size[k]: return False
    capy=1<<(5+ny-3)
    for h in range(2):
        cnt={}
        for y in range(64):
            if (y>>5)&1!=h: continue
            cnt[int(lev[y])]=cnt.get(int(lev[y]),0)+1
        for l,n in cnt.items():
            if ay[h].count(l)*capy<n: return False
    return True
best=None
for rs in range(20):
    ax=list(range(11))+list(rng.integers(0,11,5)); rng.shuffle(ax)
    ay=[list(LV)+list(rng.choice(LV,2)) for _ in range(2)]
    for h in range(2): rng.shuffle(ay[h])
    while not feasible(ax,ay):
        ax=list(range(11))+list(rng.integers(0,11,5)); rng.shuffle(ax)
    cur=cost(ax,ay)
    T=20.0
    for it in range(20000):
        T=20*(0.05/20)**(it/20000)
        nax=list(ax); nay=[list(ay[0]),list(ay[1])]
        r=rng.random()
        if r<0.35: nax[rng.integers(16)]=int(rng.integers(11))
        elif r<0.6: i,j=rng.integers(16,size=2); nax[i],nax[j]=nax[j],nax[i]
        elif r<0.8: h=rng.integers(2); nay[h][rng.integers(8)]=int(rng.choice(LV))
        else: h=rng.integers(2); i,j=rng.integers(8,size=2); nay[h][i],nay[h][j]=nay[h][j],nay[h][i]
        if not feasible(nax,nay): continue
        c=cost(nax,nay)
        if c<=cur or rng.random()<np.exp((cur-c)/T): ax,ay,cur=nax,nay,c
    if best is None or cur<best[0]: best=(cur,ax,ay); print(rs,cur,ax,ay,flush=True)
print('BEST',best)
