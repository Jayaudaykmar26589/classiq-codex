import sys, json, subprocess, numpy as np
d=np.load('ferrers.npz'); lam=d['lam']; lev=d['lev']
side=sys.argv[1]; J=json.load(open(sys.argv[2])); nanc=J['nanc']; cw=J['cw']
if side=='y':
    NP=64; mod=[sum(((v>>b)&1)<<v for v in range(64)) for b in range(5)]+[0]*nanc; ro=[sum(((v>>5)&1)<<v for v in range(64))]; want=[int(lev[v]) for v in range(64)]
else:
    NP=128; mod=[sum((((v&63)>>b)&1)<<v for v in range(128)) for b in range(6)]+[0]*nanc; ro=[sum(((v>>6)&1)<<v for v in range(128))]; want=[int(lam[v&63,v>>6]) for v in range(128)]
W=len(mod); ops=[o for o in J['ops'] if o[0]!=2]
s=f"{NP} {W} 1 {len(ops)} {len(cw)} "+" ".join(map(str,cw))+"\n"+" ".join(map(str,want))+"\n"
for t in mod+ro: s+=f"{t & ((1<<64)-1):x} {t>>64:x}\n"
for o in ops: s+=" ".join(map(str,o))+"\n"
p=subprocess.run(['./polishn'],input=s,capture_output=True,text=True,timeout=int(sys.argv[3]))
print(sys.argv[2].split('/')[-1]); print(p.stdout[-1200:])
