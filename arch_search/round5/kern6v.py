import numpy as np, itertools
H=np.array([[(-1)**bin(i&j).count('1') for j in range(8)] for i in range(8)],float)
base_x=[0,0,1,2,3,4,5,0]; base_y=[7,7,5,5,1,2,3,4]
xs=np.array(sorted(set(itertools.permutations(base_x)))); ys=np.array(sorted(set(itertools.permutations(base_y))))
best=(999,None,None); hist={}
# S[cx,cy] = 1-2*[Ly[cy] <= Lx[cx]]
for Lx in xs:
    S=1-2*(ys[:,None,:]<=Lx[None,:,None]).astype(float)       # (nY, 8(cx), 8(cy))
    W=np.einsum('ab,nbc,cd->nad',H,S,H)
    cnt=(np.abs(W)>1e-9).sum(axis=(1,2))-(np.abs(W[:,0,0])>1e-9)
    k=int(cnt.argmin())
    for c in np.unique(cnt): hist[int(c)]=hist.get(int(c),0)+int((cnt==c).sum())
    if cnt[k]<best[0]: best=(int(cnt[k]),list(Lx),list(ys[k]))
print('best parity-term count',best[0],'Lx',best[1],'Ly',best[2])
print('histogram (terms: count) lowest:',sorted(hist.items())[:8])
