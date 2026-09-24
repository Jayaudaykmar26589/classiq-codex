import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from dag import load, precedences, wires
def downset(G,prec,gens):
    pred={}
    for i,j in prec: pred.setdefault(j,[]).append(i)
    D=set(gens); st=list(gens)
    while st:
        v=st.pop()
        for p in pred.get(v,[]):
            if p not in D: D.add(p); st.append(p)
    return D
if __name__=='__main__':
    W,G=load('/home/user/classiq-codex/best_verified_depth176_cx421.qasm'); prec,_=precedences(G)
    spine=[49,50,51,67,68,69,70,71,72,73,74,75,80,81,82,86,87,88,89,90,91,102,103,104,105,122]
    for g in spine:
        D=downset(G,prec,[g]); S=sorted(set(w for i in D for w in wires(G[i])))
        nu=sum(1 for i in D if G[i][0]=='u3'); ncx=len(D)-nu
        coords=[w for w in S if w<12]
        print(g,G[g][:3],'|D|',len(D),'wires',len(S),S,'coords',len(coords),'u3',nu,'cx',ncx)
