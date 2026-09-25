import math, sys
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import parse_u3cx
import numpy as np
def u3mat(th,ph,la):
    return np.array([[math.cos(th/2), -np.exp(1j*la)*math.sin(th/2)],[np.exp(1j*ph)*math.sin(th/2), np.exp(1j*(ph+la))*math.cos(th/2)]])
Z=np.diag([1,-1]); X=np.array([[0,1],[1,0]])
def kind(p):
    U=u3mat(*p)
    if np.allclose(U@Z,Z@U,atol=1e-9): return 'D'   # diagonal: commutes with control
    if np.allclose(U@X,X@U,atol=1e-9): return 'X'   # x-axis: commutes with target
    return 'G'
def load(path):
    W,gates=parse_u3cx(open(path).read())
    G=[]
    for g in gates:
        if g[0]=='cx': G.append(('cx',g[1],g[2]))
        else: G.append(('u3',g[2],kind(g[1]),g[1]))
    return W,G
def wires(g): return (g[1],g[2]) if g[0]=='cx' else (g[1],)
def commute(a,b):
    wa=set(wires(a)); wb=set(wires(b))
    if not (wa&wb): return True
    if a[0]=='cx' and b[0]=='cx':
        return a[1]!=b[2] and a[2]!=b[1]
    if a[0]=='u3' and b[0]=='u3': return a[2]==b[2] and a[2] in 'DX'
    cx,u=(a,b) if a[0]=='cx' else (b,a)
    w=u[1]
    if w==cx[1]: return u[2]=='D'
    return u[2]=='X'
def precedences(G):
    # all same-wire non-commuting pairs (i<j), and commuting same-wire pairs (exclusive)
    n=len(G); onw={}
    for i,g in enumerate(G):
        for w in wires(g): onw.setdefault(w,[]).append(i)
    prec=set(); excl=set()
    for w,lst in onw.items():
        for a in range(len(lst)):
            for b in range(a+1,len(lst)):
                i,j=lst[a],lst[b]
                if commute(G[i],G[j]): excl.add((i,j))
                else: prec.add((i,j))
    return prec,excl
if __name__=='__main__':
    W,G=load(sys.argv[1])
    from collections import Counter
    print('gates',len(G),Counter((g[0],g[2]) if g[0]=='u3' else 'cx' for g in G))
    prec,excl=precedences(G)
    print('prec pairs',len(prec),'excl pairs',len(excl))
    # longest path over prec only
    succ={}
    for i,j in prec: succ.setdefault(i,[]).append(j)
    asap=[1]*len(G)
    for i in range(len(G)):
        for j in succ.get(i,[]):
            if asap[i]+1>asap[j]: asap[j]=asap[i]+1
    print('relaxed (commutation, no exclusivity) depth',max(asap))
