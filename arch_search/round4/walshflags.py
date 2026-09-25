import numpy as np, sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
import s2_natural_decomposition as N
def wsupp(tt,n):
    v=np.array([1-2*tt[i] for i in range(1<<n)],dtype=np.int64)
    h=1
    while h<len(v):
        for i in range(0,len(v),2*h):
            a=v[i:i+h].copy(); b=v[i+h:i+2*h].copy(); v[i:i+h]=a+b; v[i+h:i+2*h]=a-b
        h*=2
    return int((v!=0).sum())
Y=[[N.Y(j)(y) for y in range(64)] for j in range(6)]
X=[[N.X(j)(z&63,z>>6) for z in range(128)] for j in range(6)]
print('Y supports',[wsupp(t,6) for t in Y])
print('X supports',[wsupp(t,7) for t in X])
# best elements of spans
import itertools
def span_best(T,n):
    res=[]
    for m in range(1,64):
        t=[0]*(1<<n)
        for j in range(6):
            if m>>j&1: t=[a^b for a,b in zip(t,T[j])]
        res.append((wsupp(t,n),m))
    res.sort(); return res[:12]
print('Y span best',span_best(Y,6))
print('X span best',span_best(X,7))
