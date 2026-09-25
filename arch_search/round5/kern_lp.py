"""Sparse kernel with don't-cares: find real a_S (S over bits of [y-lane state (8 bits incl. h) , x-code (3 bits)])
with sum_S a_S (-1)^{S.z} = g(z) on reachable z, min L1.  Support = number of parity rotations."""
import sys, json, numpy as np
from scipy.optimize import linprog
d=np.load('ferrers.npz'); lev=d['lev']
J=json.load(open(sys.argv[1])); nanc=J['nanc']; cw=J['cw']
states=[]; levs=[]
for v in range(64):
    w=[(v>>b)&1 for b in range(5)]+[0]*nanc+[(v>>5)&1]
    for k,t,a,na,b,nb in J['ops']:
        if k==2: continue
        A=w[a]^na
        if k==0: w[t]^=A
        else: w[t]^=A&(w[b]^nb)
    states.append(sum(bit<<i for i,bit in enumerate(w))); levs.append(int(lev[v]))
ny=5+nanc+1; Lx=[0,0,0,1,2,3,4,5]; nx=3; n=ny+nx
Z=[]; G=[]
for s,l in zip(states,levs):
    for cx in range(8): Z.append(s | (cx<<ny)); G.append(1.0 if l<=Lx[cx] else 0.0)
Z=np.array(Z); G=np.array(G); N=1<<n
# design matrix chi[z,S] = (-1)^{popcount(z&S)}
S=np.arange(N)
pc=np.vectorize(lambda v: bin(v).count('1')&1)
Chi=1-2*pc(Z[:,None]&S[None,:]).astype(float)
# LP: a = p - q, minimize sum(p+q), Chi (p - q) = G
m=len(Z); c=np.ones(2*N)
res=linprog(c,A_eq=np.hstack([Chi,-Chi]),b_eq=G,bounds=(0,None),method='highs')
a=res.x[:N]-res.x[N:]; supp=int((np.abs(a)>1e-9).sum()); nz0=int(abs(a[0])>1e-9)
print('y-lane bits',ny,'x bits',nx,'reachable pts',m,'LP status',res.status,'support',supp-nz0,'(non-constant parity rotations)')
# compare: code-only representation support
