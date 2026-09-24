import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from dag import load, precedences
from satsched import windows
from rewrite import solve
W,G=load(sys.argv[1]); T=175
prec,excl=precedences(G)
asap,alap=windows(len(G),prec,T)
crit=[i for i in range(len(G)) if asap[i]==alap[i]]
lo,hi=int(sys.argv[2]),int(sys.argv[3])
for i in crit[lo:hi]:
    G2=[g for k,g in enumerate(G) if k!=i]
    lay,st=solve(G2,T)
    if lay is not None: print('UNLOCK',i,G[i][:3],'layer',asap[i],flush=True)
print('done',lo,hi,flush=True)
