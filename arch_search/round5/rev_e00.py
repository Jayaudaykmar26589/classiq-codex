"""Reverse-engineer E00: track per-input support through the gate list; report cuts where every input is a single basis state."""
import sys, numpy as np, math
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import parse_u3cx
from sparse_verify import u3mat
W,gates=parse_u3cx(open('/home/user/classiq-codex/best_verified_depth176_cx421.qasm').read())
inp=np.arange(4096,dtype=np.int64); bas=np.arange(4096,dtype=np.int64); amp=np.ones(4096,complex)
clean=[]
for k,g in enumerate(gates):
    if g[0]=='cx':
        c,t=g[1],g[2]; bas=bas^(((bas>>c)&1)<<t)
    else:
        q=g[2]; a,b,cc,d=u3mat(*g[1]); bit=(bas>>q)&1; b0=bas&~(1<<q)
        a0=np.where(bit==0,a,b)*amp; a1=np.where(bit==0,cc,d)*amp
        key=np.concatenate([(inp<<18)|b0,(inp<<18)|(b0|(1<<q))]); val=np.concatenate([a0,a1])
        o=np.argsort(key,kind='stable'); key=key[o]; val=val[o]
        uk,st=np.unique(key,return_index=True); sv=np.add.reduceat(val,st); keep=np.abs(sv)>1e-12
        uk=uk[keep]; sv=sv[keep]; inp=uk>>18; bas=uk&((1<<18)-1); amp=sv
    if len(inp)==4096: clean.append(k+1)
print('total gates',len(gates),'classical cuts (after gate index):',len(clean))
# compress into ranges
rng=[]; s=clean[0]; p=clean[0]
for c in clean[1:]:
    if c!=p+1: rng.append((s,p)); s=c
    p=c
rng.append((s,p)); print(rng[:60])
np.save('rev_clean.npy',np.array(clean))
