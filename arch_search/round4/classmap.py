import sys, numpy as np, cmath, math
sys.path.insert(0,__import__('os').path.dirname(__file__))
from refit import *
W,G=load('/home/user/classiq-codex/best_verified_depth176_cx421.qasm'); prec,_=precedences(G)
gen=int(sys.argv[1])
D=downset(G,prec,[gen]); Wn=Window(G,D)
p=[]
for g in Wn.gates:
    if g[0]=='u3': p+=list(g[3])
T=Wn.run(Wn.gates,np.array(p)); B=Wn.B; flat=T.reshape(B,-1)
print('wires',Wn.S,'coords(in order of input bits)',Wn.coords)
ph0=None
for b in range(B):
    idx=int(np.argmax(np.abs(flat[b]))); amp=flat[b][idx]
    bits=[(idx>>(Wn.n-1-k))&1 for k in range(Wn.n)]
    inp={w:(b>>k)&1 for k,w in enumerate(Wn.coords)}
    out={w:bits[Wn.loc[w]] for w in Wn.S}
    if ph0 is None: ph0=cmath.phase(amp)
    ph=(cmath.phase(amp)-ph0)/(math.pi/4)
    print('in',''.join(str(inp[w]) for w in Wn.coords),'out',' '.join('%d:%d'%(w,out[w]) for w in Wn.S),'phase/(pi/4) %.3f'%ph, 'mag %.3f'%abs(amp))
