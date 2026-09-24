import sys, itertools
sys.path.insert(0,__import__('os').path.dirname(__file__))
from dag import load, precedences, wires, commute
from satsched import windows, build
from pysat.solvers import Solver
def topo_adjacent(G,prec,g1,g2):
    n=len(G); pred={i:set() for i in range(n)}
    for i,j in prec: pred[j].add(i)
    # ancestors of g1,g2
    anc=set(); stack=[g1,g2]
    while stack:
        v=stack.pop()
        for p in pred[v]:
            if p not in anc: anc.add(p); stack.append(p)
    assert g1 not in anc and g2 not in anc
    order=sorted(anc)+[g1,g2]+[i for i in range(n) if i not in anc and i not in (g1,g2)]
    # verify it's a linear extension
    pos={v:k for k,v in enumerate(order)}
    for i,j in prec: assert pos[i]<pos[j],(i,j)
    return order
def apply_fanout(G,prec,g1,g2,hub):
    order=topo_adjacent(G,prec,g1,g2)
    c=G[g1][1]; t1=G[g1][2]; t2=G[g2][2]; assert G[g2][1]==c
    h,o=(t1,t2) if hub==0 else (t2,t1)
    rep=[('cx',h,o),('cx',c,h),('cx',h,o)]
    out=[]
    for v in order:
        if v==g1: out+=rep
        elif v==g2: continue
        else: out.append(G[v])
    return out
def solve(G,T):
    prec,excl=precedences(G)
    r=build(G,T,prec,excl)
    if r is None: return None,'window'
    cls,vid,asap,alap,y=r
    if any(len(c)==0 for c in cls):
        bad=[(i,j) for i,j in excl if asap[i]==alap[i]==asap[j]==alap[j]]
        return None,('forced',[(i,G[i],j,G[j],asap[i]) for i,j in bad])
    with Solver(name='cd19',bootstrap_with=cls) as s:
        if not s.solve(): return None,'UNSAT'
        m=set(l for l in s.get_model() if l>0)
        lay=[]
        for i in range(len(G)):
            t=asap[i]
            while t<alap[i] and y(i,t) not in m: t+=1
            lay.append(t)
        return lay,'SAT'
if __name__=='__main__':
    path=sys.argv[1]; T=int(sys.argv[2])
    W,G=load(path)
    prec,_=precedences(G)
    pairs=[(372,405),(483,490)]
    for hubs in itertools.product([0,1],repeat=2):
        G2=list(G)
        # apply second rewrite first (higher indices) so indices of first stay valid
        p2=precedences(G2)[0]
        G2=apply_fanout(G2,p2,483,490,hubs[1])
        # locate first pair again by content order: indices 372,405 unaffected? recompute by search
        p2=precedences(G2)[0]
        # original gates 372,405 keep content; find their new indices
        idx=[k for k,g in enumerate(G2) if g==G[372]]; idx2=[k for k,g in enumerate(G2) if g==G[405]]
        # choose indices closest to original
        a=min(idx,key=lambda k:abs(k-372)); b=min(idx2,key=lambda k:abs(k-405))
        G3=apply_fanout(G2,p2,a,b,hubs[0])
        lay,st=solve(G3,T)
        print('hubs',hubs,'cx',sum(g[0]=='cx' for g in G3),st if lay is None else 'SAT', flush=True)
        if lay is not None:
            import pickle; pickle.dump((G3,lay),open('sched/sol_T%d_%d%d.pkl'%(T,*hubs),'wb'))
