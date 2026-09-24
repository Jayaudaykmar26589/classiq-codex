import sys, numpy as np, itertools
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import logo_pixel
M=np.array([[logo_pixel(x,y) for y in range(64)] for x in range(64)],dtype=int)  # M[x,y]
def swap(y): return y ^ (32 if ((y>>4)&1 and (y>>3)&1 and (y>>2)&1) else 0)   # y5 ^= y4 y3 y2
Ms=np.zeros_like(M,dtype=int)
for y in range(64): Ms[:,swap(y)]=M[:,y]      # logo in new coordinates y'
ok=True; lam=np.zeros((64,2),int); lev=np.zeros(64,int)
for h in (0,1):
    ys=[y for y in range(64) if (y>>5)==h]
    rows={}
    for y in ys: rows.setdefault(tuple(int(v) for v in Ms[:,y]),[]).append(y)
    pats=sorted(rows, key=lambda p: -sum(p))      # biggest row pattern first
    nested=all(all(a>=b for a,b in zip(pats[i],pats[i+1])) for i in range(len(pats)-1))
    print('half',h,'row classes',len(pats),'sizes',[len(rows[p]) for p in pats],'nested chain:',nested)
    ok&=nested
    # levels: row level l = index in chain (1 = widest); empty row -> big
    for i,p in enumerate(pats):
        for y in rows[p]: lev[y]= (i+1) if sum(p)>0 else 7
    for x in range(64):
        # column level = number of nonempty patterns containing x
        lam[x,h]=sum(1 for p in pats if sum(p)>0 and p[x])
# check f == [lam(x,h) >= lev(y)] with chain ordered widest=1 -> x in pattern i iff lam >= ... 
bad=0
for x in range(64):
    for y in range(64):
        h=y>>5; v= int(lev[y]<=7 and lev[y]!=7 and lam[x,h] >= (len([1])*0) )
# explicit: x in row pattern of level l  <=> lam(x,h) >= (#nonempty patterns) - l + 1
for h in (0,1):
    ys=[y for y in range(64) if (y>>5)==h]; K=max(lev[y] for y in ys if lev[y]!=7)
    for x in range(64):
        for y in ys:
            pred = lev[y]!=7 and lam[x,h] >= K-lev[y]+1
            bad += int(pred)!=Ms[x,y]
print('Ferrers comparator mismatches:',bad)
print('lambda(x,0) values',sorted(set(lam[:,0])),'lambda(x,1)',sorted(set(lam[:,1])))
np.savez('ferrers.npz',lam=lam,lev=lev)
