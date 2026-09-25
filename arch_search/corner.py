"""Corner representation: f(x,y) = XOR_{(i,j): Delta f=1} [x>=j][y>=i]."""
import sys, os, numpy as np
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grader import logo_pixel
F = np.array([[logo_pixel(x,y) for x in range(64)] for y in range(64)], dtype=np.uint8)  # F[y,x]
P = np.zeros((65,65),dtype=np.uint8); P[1:,1:]=F
D = (P[1:,1:]^P[:-1,1:]^P[1:,:-1]^P[:-1,:-1])      # D[i,j] for y>=i, x>=j
corners = [(i,j) for i in range(64) for j in range(64) if D[i,j]]
xs = sorted(set(j for i,j in corners)); ys = sorted(set(i for i,j in corners))
C = np.zeros((len(xs),len(ys)),dtype=np.uint8)
for i,j in corners: C[xs.index(j), ys.index(i)] = 1
def rank2(M):
    M=M.copy()%2; r=0; rows,cols=M.shape
    for c in range(cols):
        p=[k for k in range(r,rows) if M[k,c]]
        if not p: continue
        M[[r,p[0]]]=M[[p[0],r]]
        for k in range(rows):
            if k!=r and M[k,c]: M[k]^=M[r]
        r+=1
        if r==rows: break
    return r
def u(t): return np.array([int(x>=t) for x in range(64)],dtype=np.uint8)
if __name__=='__main__':
    print('corners',len(corners),'x-thresholds',len(xs),xs)
    print('y-thresholds',len(ys),ys)
    print('rank C',rank2(C),'rank F',rank2(F))
    print('max degree x',C.sum(1).max(),'y',C.sum(0).max())
    # reconstruct check
    R=np.zeros((64,64),dtype=np.uint8)
    for i,j in corners: R[i:,j:]^=1
    print('reconstruct ok', (R==F).all())
