import numpy as np, sys
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import logo_pixel
from collections import Counter
M=np.array([[logo_pixel(x,y) for y in range(64)] for x in range(64)],dtype=np.uint8)
M0=M[:,:32]; M1=M[:,32:]
def rref(A):
    A=A.copy()%2; r=0
    for c in range(A.shape[1]):
        p=None
        for i in range(r,A.shape[0]):
            if A[i,c]: p=i;break
        if p is None: continue
        A[[r,p]]=A[[p,r]]
        for i in range(A.shape[0]):
            if i!=r and A[i,c]: A[i]^=A[r]
        r+=1
        if r==A.shape[0]: break
    return A[:r]
def anf(tt):
    a=np.array(tt,dtype=np.uint8).copy(); n=len(a).bit_length()-1
    for i in range(n):
        s=1<<i
        for j in range(len(a)):
            if j&s: a[j]^=a[j^s]
    return a
def deg(tt):
    a=anf(tt); d=-1
    for j in np.nonzero(a)[0]: d=max(d,bin(j).count('1'))
    return d
def span_hist(B,name):
    k=len(B); h=Counter()
    for m in range(1,1<<k):
        v=np.zeros(B.shape[1],dtype=np.uint8)
        for i in range(k):
            if m>>i&1: v^=B[i]
        h[deg(v)]+=1
    print(name,'dim',k,'deg hist',dict(sorted(h.items())))
R0=rref(M0.T.copy()); R1=rref(M1.T.copy())  # hmm rows: want row space over y -> rows of M0^T? 
# M0[x][y']: row space over y' = span of rows M0[x,:]
R0=rref(M0); R1=rref(M1)          # functions of y' (32)
C0=rref(M0.T); C1=rref(M1.T)      # functions of x (64)
span_hist(R0,'R0 (y lower)'); span_hist(R1,'R1 (y upper)')
span_hist(C0,'C0 (x lower)'); span_hist(C1,'C1 (x upper)')
np.savez('halves.npz',M=M,R0=R0,R1=R1,C0=C0,C1=C1)
