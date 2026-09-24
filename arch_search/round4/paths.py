import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from dag import load, precedences, wires
from satsched import windows
W,G=load(sys.argv[1]); T=175
prec,excl=precedences(G)
n=len(G); asap,alap=windows(n,prec,T)
pred={i:[] for i in range(n)}; succ={i:[] for i in range(n)}
for i,j in prec: pred[j].append(i); succ[i].append(j)
def up(g):  # one critical upstream chain
    ch=[g]
    while True:
        ps=[p for p in pred[ch[-1]] if asap[p]==asap[ch[-1]]-1]
        if not ps: break
        ch.append(ps[0])
    return ch[::-1]
def down(g):
    ch=[g]
    while True:
        ss=[s for s in succ[ch[-1]] if alap[s]==alap[ch[-1]]+1]
        if not ss: break
        ch.append(ss[0])
    return ch
def fmt(i):
    g=G[i]; return f"{i}:{'cx%d>%d'%(g[1],g[2]) if g[0]=='cx' else 'u%s@%d'%(g[2],g[1])}"
for g in map(int,sys.argv[2:]):
    print('UP to',fmt(g),' '.join(fmt(i) for i in up(g)))
    print('DOWN from',fmt(g),' '.join(fmt(i) for i in down(g)))
# count number of distinct upstream critical predecessors (branching)
