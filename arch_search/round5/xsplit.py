import sys, itertools, numpy as np
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import logo_pixel
M=np.array([[logo_pixel(x,y) for y in range(64)] for x in range(64)],dtype=int)
need1=[x for x in range(32,49)]                    # C2 columns -> group B
need0=[x for x in range(2,27)]+[x for x in range(50,61)]   # R1 + C1 core columns -> group A
free=[x for x in range(64) if x not in need1 and x not in need0]
print('free columns',free)
# enumerate g of degree <= 3 as XOR of monomials is huge; instead enumerate products of up to 3 literals/affine forms
def val(g): return [g(x) for x in range(64)]
best=[]
lits=[(lambda b,s: (lambda x: ((x>>b)&1)^s))(b,s) for b in range(6) for s in (0,1)]
aff=[]
for m in range(1,64):
    for c in (0,1):
        aff.append((m,c))
def affv(m,c): return np.array([ (bin(x&m).count('1')+c)&1 for x in range(64)])
A=[affv(m,c) for m,c in aff]
ok=[]
# g = a1 & a2 (degree 2) or a1 & a2 & a3 (degree 3) or a1 ^ (a2 & a3)
N1=np.array(need1); N0=np.array(need0)
for i in range(len(A)):
    for j in range(i,len(A)):
        g=A[i]&A[j]
        if g[N1].all() and not g[N0].any(): ok.append(('and2',aff[i],aff[j]))
print('degree-2 products that split:',len(ok), ok[:5])
cnt=0
for i in range(len(A)):
    for j in range(i,len(A)):
        gij=A[i]&A[j]
        if not gij[N1].all(): continue
        for k in range(j,len(A)):
            g=gij&A[k]
            if g[N1].all() and not g[N0].any():
                cnt+=1
                if cnt<=5: print('and3 split',aff[i],aff[j],aff[k])
print('degree-3 products that split:',cnt)
