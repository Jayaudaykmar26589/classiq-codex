"""GL(10,2) basis search for f = XOR_k A_k(x) B_k(y) starting from the corner factorization."""
import numpy as np, random, sys
from corner import C, xs, ys, rank2
def anf(tt):
    a=np.array(tt,dtype=np.uint8).copy()
    for i in range(6):
        for m in range(64):
            if m>>i&1: a[m]^=a[m^(1<<i)]
    return a
POP=np.array([bin(m).count('1') for m in range(64)])
def cost(tt):
    a=anf(tt); mons=np.nonzero(a)[0]
    if len(mons)==0: return 0.0
    d=POP[mons].max()
    return max(d-1,0) + 0.02*len(mons)
def factor(C):
    """C (19x20) = P Q^T with rank r: row-reduce C to get independent rows basis."""
    M=C.copy()%2; rows,cols=M.shape
    # choose r independent columns of C as B-basis (y side): C = P Q^T where Q^T = selected rows of RREF
    R=M.copy(); piv=[]; r=0; T=np.eye(rows,dtype=np.uint8)
    for c in range(cols):
        p=[k for k in range(r,rows) if R[k,c]]
        if not p: continue
        R[[r,p[0]]]=R[[p[0],r]]; T[[r,p[0]]]=T[[p[0],r]]
        for k in range(rows):
            if k!=r and R[k,c]: R[k]^=R[r]; T[k]^=T[r]
        piv.append(c); r+=1
    QT=R[:r]            # r x 20
    # C = P QT  -> solve P: rows of C in span of QT rows; P[i] = coefficients = C[i, piv]
    P=C[:,piv]%2
    assert ((P.astype(int)@QT.astype(int))%2==C).all()
    return P, QT.T.copy()
U=np.array([[int(x>=t) for x in range(64)] for t in xs],dtype=np.uint8)   # 19 x 64
V=np.array([[int(y>=s) for y in range(64)] for s in ys],dtype=np.uint8)   # 20 x 64
def funcs(P,Q):
    A=(P.T.astype(int)@U.astype(int))%2   # 10 x 64
    B=(Q.T.astype(int)@V.astype(int))%2
    return A.astype(np.uint8),B.astype(np.uint8)
def total(A,B,mode='max'):
    ca=[cost(a) for a in A]; cb=[cost(b) for b in B]
    return sum(max(p,q) for p,q in zip(ca,cb)) if mode=='max' else sum(ca)+sum(cb)
def anneal(P,Q,iters=20000,T0=1.0,seed=0,mode='max'):
    rng=random.Random(seed); A,B=funcs(P,Q)
    ca=[cost(a) for a in A]; cb=[cost(b) for b in B]
    cur=sum(max(p,q) for p,q in zip(ca,cb)) if mode=='max' else sum(ca)+sum(cb)
    best=(cur,A.copy(),B.copy())
    for it in range(iters):
        T=T0*(1-it/iters)+1e-3
        i,j=rng.sample(range(10),2)
        na=A[i]^A[j]; nb=B[j]^B[i]
        if not na.any() or not nb.any(): continue
        c1=cost(na); c2=cost(nb)
        oa,ob=ca[i],cb[j]
        ca[i],cb[j]=c1,c2
        new=sum(max(p,q) for p,q in zip(ca,cb)) if mode=='max' else sum(ca)+sum(cb)
        if new<=cur or rng.random()<np.exp((cur-new)/T):
            A[i]=na; B[j]=nb; cur=new
            if cur<best[0]: best=(cur,A.copy(),B.copy())
        else: ca[i],cb[j]=oa,ob
    return best
def check(A,B):
    from grader import TARGET
    M=np.zeros((64,64),dtype=np.uint8)
    for a,b in zip(A,B): M^=np.outer(b,a)
    return (M.flatten()==TARGET.astype(np.uint8)).all()
if __name__=='__main__':
    sys.path.insert(0,'..')
    P,Q=factor(C); A,B=funcs(P,Q)
    print('initial valid',check(A,B),'cost',round(total(A,B),2))
    res=[]
    for seed in range(int(sys.argv[1]) if len(sys.argv)>1 else 6):
        b=anneal(P,Q,iters=30000,seed=seed)
        res.append(b); print('seed',seed,'cost',round(b[0],2),'valid',check(b[1],b[2]),flush=True)
    b=min(res,key=lambda r:r[0])
    np.save('rb_best_A.npy',b[1]); np.save('rb_best_B.npy',b[2])
    for a,bb in zip(b[1],b[2]):
        da=anf(a); db=anf(bb)
        print('A deg',POP[np.nonzero(da)[0]].max(),'#1s',a.sum(),' B deg',POP[np.nonzero(db)[0]].max(),'#1s',bb.sum())
