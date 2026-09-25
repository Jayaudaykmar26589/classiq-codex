import sys, json, numpy as np
d=np.load('ferrers.npz'); lev=d['lev']
J=json.load(open(sys.argv[1])); nanc=J['nanc']; cw=J['cw']
Ly={}
for v in range(64):
    w=[(v>>b)&1 for b in range(5)]+[0]*nanc+[(v>>5)&1]
    for k,t,a,na,b,nb in J['ops']:
        if k==2: continue
        A=w[a]^na
        if k==0: w[t]^=A
        else: w[t]^=A&(w[b]^nb)
    c=sum(w[cw[i]]<<i for i in range(len(cw))); Ly[c]=int(lev[v])
nby=len(cw); print('y code bits',nby,'codes',len(Ly))
def fwht(a):
    a=a.astype(float).copy(); h=1
    while h<len(a):
        a=a.reshape(-1,2*h); u=a[:,:h].copy(); v2=a[:,h:].copy(); a[:,:h]=u+v2; a[:,h:]=u-v2; a=a.reshape(-1); h*=2
    return a
for Lx in ([0,0,0,1,2,3,4,5],[0,1,2,3,4,5,0,0],[5,4,3,2,1,0,0,0]):
    nbx=3
    g=np.array([1 if Ly.get(cy,99)<=Lx[cx] else 0 for cy in range(1<<nby) for cx in range(1<<nbx)])  # index cy*8+cx
    w=fwht(1-2*g); print('Lx',Lx,'kernel phase terms',int((np.abs(w)>1e-9).sum())-1)
