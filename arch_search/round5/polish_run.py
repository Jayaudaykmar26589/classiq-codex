import sys, json, subprocess, numpy as np
d=np.load('ferrers.npz'); lev=d['lev']
J=json.load(open(sys.argv[1])); nanc=J['nanc']
mod=[sum(((v>>b)&1)<<v for v in range(64)) for b in range(5)]+[0]*nanc; ro=[sum(((v>>5)&1)<<v for v in range(64))]
W=len(mod); ops=[o for o in J['ops'] if o[0]!=2]
s=f"64 {W} 1 {len(ops)} {J['cw'][0]} {J['cw'][1]} {J['cw'][2]}\n"+" ".join(str(int(lev[v])) for v in range(64))+"\n"
for t in mod+ro: s+=f"{t:x} 0\n"
for o in ops: s+=" ".join(map(str,o))+"\n"
p=subprocess.run(['./polish'],input=s,capture_output=True,text=True,timeout=int(sys.argv[2]))
print(sys.argv[1].split('/')[-1]); print(p.stdout[-1500:])
