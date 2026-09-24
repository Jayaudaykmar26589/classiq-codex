import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from dag import load, precedences, wires
from satsched import windows
W,G=load(sys.argv[1]); T=int(sys.argv[2])
prec,excl=precedences(G)
asap,alap=windows(len(G),prec,T)
crit=[i for i in range(len(G)) if asap[i]==alap[i]]
print('zero-slack gates',len(crit))
for i,j in sorted(excl):
    if asap[i]==alap[i]==asap[j]==alap[j]:
        print('FORCED CONFLICT layer',asap[i],i,G[i][:3],j,G[j][:3])
# per wire slack view near conflicts
