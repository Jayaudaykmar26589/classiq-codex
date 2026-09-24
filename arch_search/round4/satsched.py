import sys, time
sys.path.insert(0,__import__('os').path.dirname(__file__))
from dag import load, precedences, wires
from pysat.solvers import Solver
def windows(n,prec,T):
    succ={};pred={}
    for i,j in prec: succ.setdefault(i,[]).append(j); pred.setdefault(j,[]).append(i)
    asap=[1]*n
    for i in range(n):
        for j in succ.get(i,[]): asap[j]=max(asap[j],asap[i]+1)
    alap=[T]*n
    for i in reversed(range(n)):
        for j in succ.get(i,[]): alap[i]=min(alap[i],alap[j]-1)
    return asap,alap
def build(G,T,prec,excl,extra_excl_soft=False):
    n=len(G); asap,alap=windows(n,prec,T)
    if any(asap[i]>alap[i] for i in range(n)): return None
    vid={}; cnt=[0]
    def y(i,t):  # [t(i) <= t]
        if t<asap[i]: return -TRUE
        if t>=alap[i]: return TRUE
        k=(i,t)
        if k not in vid: cnt[0]+=1; vid[k]=cnt[0]+1
        return vid[k]
    TRUE=1
    cls=[[TRUE]]
    for i in range(n):
        for t in range(asap[i],alap[i]):
            if t>asap[i]: cls.append([-y(i,t-1),y(i,t)])
    for i,j in prec:   # t(i) < t(j): y(j,t) -> y(i,t-1)
        for t in range(asap[j],alap[j]+1):
            a=y(j,t); b=y(i,t-1)
            if a==-TRUE or b==TRUE: continue
            cls.append([-a,b])
    soft=[]
    for i,j in excl:
        lo=max(asap[i],asap[j]); hi=min(alap[i],alap[j])
        for t in range(lo,hi+1):
            c=[]
            for (g,s) in ((i,t),(j,t)):
                c+= [-y(g,s), y(g,s-1)]
            c=[l for l in c if l!=-TRUE]
            if TRUE in c: continue
            cls.append(c)
    return cls,vid,asap,alap,y
if __name__=='__main__':
    W,G=load(sys.argv[1]); T=int(sys.argv[2])
    prec,excl=precedences(G)
    t0=time.time(); r=build(G,T,prec,excl)
    if r is None: print('window infeasible'); sys.exit()
    cls,vid,asap,alap,y=r
    print('vars',len(vid),'clauses',len(cls),'build',round(time.time()-t0,1),flush=True)
    with Solver(name='cd19',bootstrap_with=cls) as s:
        ok=s.solve(); print('T',T,'SAT' if ok else 'UNSAT','time',round(time.time()-t0,1))
