"""Refined-code feasibility: find c: 64 -> 16 (4-bit code) that REFINES the logo classes
(different classes -> different codes), each code value holds <= CAP inputs (in-place with separators),
minimising the ANF degree of the 4 code bits.  Necessary condition for AND-depth-2 encoders: max degree <= 4."""
import sys, numpy as np
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import logo_pixel
M=np.array([[logo_pixel(x,y) for y in range(64)] for x in range(64)],dtype=np.uint8)
axis=sys.argv[1]; CAP=int(sys.argv[2]); seed=int(sys.argv[3]); NB=int(sys.argv[4]) if len(sys.argv)>4 else 4
A=M if axis=='x' else M.T
cls={}; lab=np.zeros(64,int)
for i in range(64): lab[i]=cls.setdefault(tuple(A[i]),len(cls))
def anfdeg(tt):
    a=tt.copy()
    for i in range(6):
        s=1<<i
        for j in range(64):
            if j&s: a[j]^=a[j^s]
    nz=np.nonzero(a)[0]
    return max((bin(j).count('1') for j in nz),default=-1)
NC=1<<NB
def cost(c):
    # violations: code shared by different classes; overflow
    v=0
    for k in range(NC):
        m=c==k; n=m.sum()
        if n==0: continue
        v+=len(set(lab[m]))-1
        v+=max(0,n-CAP)
    degs=[anfdeg(((c>>b)&1).astype(np.uint8)) for b in range(NB)]
    return 100*v+sum(max(0,d-2)**2 for d in degs), v, degs
rng=np.random.default_rng(seed)
# init: assign classes greedily to codes
c=np.zeros(64,int); nxt=0
for L in range(len(cls)):
    idx=np.nonzero(lab==L)[0]
    for t in range(0,len(idx),CAP): c[idx[t:t+CAP]]=nxt%NC; nxt+=1
cur,v,d=cost(c); best=(cur,c.copy(),v,d)
T0,T1,N=5.0,0.05,int(sys.argv[5]) if len(sys.argv)>5 else 40000
for it in range(N):
    T=T0*(T1/T0)**(it/N); c2=c.copy()
    if rng.random()<0.5: c2[rng.integers(64)]=rng.integers(NC)
    else:
        i,j=rng.integers(64,size=2); c2[i],c2[j]=c2[j],c2[i]
    n,v2,d2=cost(c2)
    if n<=cur or rng.random()<np.exp((cur-n)/T): c,cur,v,d=c2,n,v2,d2
    if cur<best[0]: best=(cur,c.copy(),v,d)
print(axis,'CAP',CAP,'bits',NB,'seed',seed,'best cost',best[0],'violations',best[2],'code-bit degrees',best[3],'codes used',len(set(best[1])))
np.save(f'code_{axis}_{CAP}_{NB}_{seed}.npy',best[1])
