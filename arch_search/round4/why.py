import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from dag import load, precedences, wires
from satsched import windows
W,G=load(sys.argv[1]); T=int(sys.argv[2])
prec,excl=precedences(G)
asap,alap=windows(len(G),prec,T)
pred={};succ={}
for i,j in prec: pred.setdefault(j,[]).append(i); succ.setdefault(i,[]).append(j)
for g in map(int,sys.argv[3:]):
    print('gate',g,G[g][:3],'asap',asap[g],'alap',alap[g])
    ps=[p for p in pred.get(g,[]) if asap[p]==asap[g]-1]
    ss=[s for s in succ.get(g,[]) if alap[s]==alap[g]+1]
    for p in ps: print('   tight pred',p,G[p][:3],'wires shared',set(wires(G[p]))&set(wires(G[g])),'asap',asap[p],'alap',alap[p])
    for s in ss: print('   tight succ',s,G[s][:3],'wires shared',set(wires(G[s]))&set(wires(G[g])),'asap',asap[s],'alap',alap[s])
# per-wire timeline window around layers
for w in [10,14,15,16]:
    ev=sorted([(asap[i],alap[i],i,G[i][:3]) for i in range(len(G)) if w in wires(G[i]) and 74<=asap[i]<=94])
    print('wire',w,[(a,b,i,g[0] if g[0]=='u3' else ('C' if g[1]==w else 'T')+str(g[2] if g[1]==w else g[1])) for a,b,i,g in ev])
