"""Driver for /tmp/claude-0/mt/lanex (SA prefix + exact final AND level)."""
import subprocess
BIN="/tmp/claude-0/mt/lanex"
def tt_split(t): return (t & ((1<<64)-1), t >> 64)
def search(NP, mod_init, ro_init, targets, L, maxlev, iters=200000, restarts=4, seed=1, lam=0.02, timeout=None):
    W=len(mod_init); R=len(ro_init)
    s=f"{NP} {W} {R} {len(targets)} {L} {maxlev} {iters} {restarts} {seed} {lam}\n"
    for t in targets: a,b=tt_split(t); s+=f"{a:x} {b:x}\n"
    for t in list(mod_init)+list(ro_init): a,b=tt_split(t); s+=f"{a:x} {b:x}\n"
    out=subprocess.run([BIN],input=s,capture_output=True,text=True,timeout=timeout).stdout
    lines=out.strip().split("\n"); head=lines[0].split()
    ops=[tuple(map(int,l.split()[1:])) for l in lines if l.startswith("OP")]
    fin=[tuple(map(int,l.split()[1:])) for l in lines if l.startswith("FIN")]
    return int(head[1]), head, ops, fin
def run(NP, mod_init, ro_init, ops, fin):
    ONE=(1<<NP)-1; v=list(mod_init)+list(ro_init)
    for k,t,a,na,b,nb in ops:
        if k==2: continue
        A=v[a]^(ONE if na else 0)
        if k==0: v[t]^=A
        else: v[t]^=A&(v[b]^(ONE if nb else 0))
    for t,a,b in fin:
        if a>=0: v[t]^=v[a]&v[b]
    return v
def in_span(vecs, t, ONE):
    basis={}
    for x in list(vecs)+[ONE]:
        while x:
            p=x&-x
            if p in basis: x^=basis[p]
            else: basis[p]=x; break
    while t:
        p=t&-t
        if p in basis: t^=basis[p]
        else: return False
    return True
def check(NP, mod_init, ro_init, ops, fin, targets):
    ONE=(1<<NP)-1; v=run(NP,mod_init,ro_init,ops,fin)
    return all(in_span(v,t,ONE) for t in targets)
