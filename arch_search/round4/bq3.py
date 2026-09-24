import sys, itertools, math, numpy as np, pickle
sys.path.insert(0,__import__('os').path.dirname(__file__))
from dag import load
from bqskit import Circuit
from bqskit.ir.gates import U3Gate, CNOTGate, ConstantUnitaryGate
from bqskit.qis import UnitaryMatrix
W,G=load('/home/user/classiq-codex/best_verified_depth176_cx421.qasm')
def u3m(t,p,l):
    c,s=math.cos(t/2),math.sin(t/2)
    return np.array([[c,-np.exp(1j*l)*s],[np.exp(1j*p)*s,np.exp(1j*(p+l))*c]])
def block_unitary(Q,idx):
    c=Circuit(3); loc={w:i for i,w in enumerate(Q)}
    for i in idx:
        g=G[i]
        if g[0]=='cx': c.append_gate(CNOTGate(),[loc[g[1]],loc[g[2]]])
        else: c.append_gate(U3Gate(),[loc[g[1]]],list(g[3]))
    return c.get_unitary()
name=sys.argv[1]
if name=='A': Q=[17,12,8]; idx=[592,593,595,594,596,597,609,610]
else: Q=[12,3,15]; idx=[670,671,732,733,734]
U=block_unitary(Q,idx)
pairs=[(a,b) for a in range(3) for b in range(3) if a!=b]
alpha=pairs+['U']
k=int(sys.argv[2]); hits=[]
for tmpl in itertools.product(alpha,repeat=k):
    if tmpl.count('U')>2: continue
    c=Circuit(3)
    for q in range(3): c.append_gate(U3Gate(),[q])
    for s in tmpl:
        if s=='U':
            for q in range(3): c.append_gate(U3Gate(),[q])
        else:
            c.append_gate(CNOTGate(),list(s)); c.append_gate(U3Gate(),[3-s[0]-s[1]])
    for q in range(3): c.append_gate(U3Gate(),[q])
    c.instantiate(U,method='minimization',multistarts=6)
    d=c.get_unitary().get_distance_from(U)
    if d<1e-7:
        print('HIT',tmpl,d,flush=True); hits.append((tmpl,c.params))
print('done',name,k,len(hits),flush=True)
pickle.dump(hits,open(f'sched/bq3_{name}_{k}.pkl','wb'))
