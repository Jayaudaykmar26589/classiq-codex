import sys, subprocess, numpy as np, json
d=np.load('ferrers.npz'); lam=d['lam']; lev=d['lev']
side=sys.argv[1]; nanc=int(sys.argv[2]); L=int(sys.argv[3]); ml=int(sys.argv[4]); seed=int(sys.argv[5]); iters=int(sys.argv[6]); fixed=int(sys.argv[7])
if side=='y':
    NP=64; mod=[sum(((v>>b)&1)<<v for v in range(64)) for b in range(5)]+[0]*nanc; ro=[sum(((v>>5)&1)<<v for v in range(64))]
    want=[int(lev[v]) for v in range(64)]; Lm=[1,2,3,4,5,5,7,7]
else:
    NP=128; mod=[sum((((v&63)>>b)&1)<<v for v in range(128)) for b in range(6)]+[0]*nanc; ro=[sum(((v>>6)&1)<<v for v in range(128))]
    want=[int(lam[v&63,v>>6]) for v in range(128)]; Lm=[0,0,0,1,2,3,4,5]
W=len(mod); NBC=int(sys.argv[8]) if len(sys.argv)>8 else 3; cw=list(range(W-NBC,W))
s=f"{NP} {W} 1 {NBC} {L} {ml} {iters} 6 {seed} 0.02 {fixed}\n"+" ".join(map(str,cw))+"\n"+" ".join(map(str,want))+"\n"
if fixed: s+=" ".join(map(str,Lm))+"\n"
for t in mod+ro: s+=f"{t & ((1<<64)-1):x} {t>>64:x}\n"
out=subprocess.run(['./lanelev'],input=s,capture_output=True,text=True).stdout.split('\n')
print(side,'nanc',nanc,'L',L,'maxlev',ml,'seed',seed,'fixed',fixed,out[0],flush=True)
if True:
    json.dump({'ops':[list(map(int,l.split()[1:])) for l in out if l.startswith('OP')],'cw':cw,'nanc':nanc},open(f'lev4_{side}_{nanc}_{L}_{ml}_{seed}_{fixed}.json','w'))
