import sys, numpy as np
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import logo_pixel
M=np.array([[logo_pixel(x,y) for y in range(64)] for x in range(64)],dtype=np.uint8)
cx=np.load(sys.argv[1]); cy=np.load(sys.argv[2]); nb=int(sys.argv[3])
N=1<<nb
g=-np.ones((N,N),int)
for x in range(64):
    for y in range(64):
        g[cx[x],cy[y]]=M[x,y]
care=g>=0; print('used x codes',len(set(cx)),'y codes',len(set(cy)),'cared entries',care.sum(),'of',N*N)
g0=np.where(care,g,0)
# Walsh support with don't-cares = 0 and GF(2) ANF term count / degree
def fwht(a):
    a=a.astype(float).copy(); h=1
    while h<len(a):
        for i in range(0,len(a),2*h):
            u=a[i:i+h].copy(); v=a[i+h:i+2*h].copy(); a[i:i+h]=u+v; a[i+h:i+2*h]=u-v
        h*=2
    return a
flat=np.array([g0[i>>nb, i&(N-1)] for i in range(N*N)])
w=fwht(1-2*flat); print('Walsh support (dc=0):',int((np.abs(w)>1e-9).sum()))
a=flat.copy().astype(np.uint8)
for i in range(2*nb):
    s=1<<i
    for j in range(N*N):
        if j&s: a[j]^=a[j^s]
nz=np.nonzero(a)[0]; from collections import Counter
print('ANF terms',len(nz),'degree hist',sorted(Counter(bin(j).count('1') for j in nz).items()))
# GF(2) rank of code matrix
def rank(A):
    A=A.copy()%2; r=0
    for c in range(A.shape[1]):
        p=[i for i in range(r,A.shape[0]) if A[i,c]]
        if not p: continue
        A[[r,p[0]]]=A[[p[0],r]]
        for i in range(A.shape[0]):
            if i!=r and A[i,c]: A[i]^=A[r]
        r+=1
    return r
print('kernel matrix rank',rank(g0.astype(np.uint8)))
