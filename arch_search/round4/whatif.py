import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from dag import load, precedences
from rewrite import solve
W,G=load(sys.argv[1]); T=int(sys.argv[2]); drop=set(map(int,sys.argv[3:]))
G2=[g for i,g in enumerate(G) if i not in drop]
lay,st=solve(G2,T)
print('drop',sorted(drop),'T',T,st if lay is None else 'SAT')
