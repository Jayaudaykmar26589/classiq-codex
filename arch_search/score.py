"""Phase-0 immutable scorer.  score(qasm_text, cid, arch, params, notes) ->
grader-exact (width, depth, cx), exact all-4096 verification, critical path report,
append to results.csv, maintain incumbents (primary = lowest depth then CX) and plateau counter."""
import sys, os, json, hashlib, csv, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grader import qasm_metrics, parse_u3cx
import sparse_verify
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results.csv'); STATE = os.path.join(HERE, 'state.json')
FIELDS = ['time','cid','arch','params','valid','width','depth','cx','S','qasm_sha','crit_len','crit_cx','crit_u3','crit_top_wires','notes']
def critical_path(src):
    W, gates = parse_u3cx(src)
    d = [0]*W; last = [None]*W; pred = []; lay = []
    for i, g in enumerate(gates):
        qs = (g[2],) if g[0]=='u3' else (g[1], g[2])
        src_q = max(qs, key=lambda q: d[q]); L = d[src_q]+1
        pred.append(last[src_q])
        for q in qs: d[q] = L; last[q] = i
        lay.append(L)
    end = max(range(len(gates)), key=lambda i: lay[i]); path=[]; i=end
    while i is not None: path.append(i); i = pred[i]
    path.reverse()
    wc = collections.Counter(); ncx = nu = 0
    for i in path:
        g = gates[i]
        if g[0]=='cx': ncx += 1; wc[g[1]] += 1; wc[g[2]] += 1
        else: nu += 1; wc[g[2]] += 1
    return len(path), ncx, nu, wc.most_common(6), path
def load_state():
    if os.path.exists(STATE): return json.load(open(STATE))
    return {'best': None, 'plateau': {}, 'tabu': []}
def score(src, cid, arch, params='', notes='', family=None, save_dir=None):
    w, d, cx = qasm_metrics(src)
    ok = bool(sparse_verify.verify(src)['passed']) if hasattr(sparse_verify,'verify') else None
    L, ccx, cu, top, _ = critical_path(src)
    sha = hashlib.sha256(src.encode()).hexdigest()[:16]
    row = dict(time=time.strftime('%Y-%m-%dT%H:%M:%S'), cid=cid, arch=arch, params=params, valid=int(bool(ok)),
               width=w, depth=d, cx=cx, S=10**6*d+cx, qasm_sha=sha, crit_len=L, crit_cx=ccx, crit_u3=cu,
               crit_top_wires=' '.join('q%d:%d'%t for t in top), notes=notes)
    new = not os.path.exists(RES)
    with open(RES,'a',newline='') as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS)
        if new: wr.writeheader()
        wr.writerow(row)
    st = load_state(); fam = family or arch
    if ok:
        b = st['best']
        if b is None or d < b['depth']:
            st['best'] = dict(cid=cid, depth=d, cx=cx, sha=sha); st['plateau'][fam] = 0
            if save_dir: open(os.path.join(save_dir, 'best_%s.qasm'%cid),'w').write(src)
        else:
            if d == b['depth'] and cx < b['cx']:
                st['best'] = dict(cid=cid, depth=d, cx=cx, sha=sha)
            st['plateau'][fam] = st['plateau'].get(fam,0) + 1
    json.dump(st, open(STATE,'w'), indent=1)
    print('[%s] %s valid=%s W=%d D=%d CX=%d | crit %d (cx %d, u3 %d) top %s | family %s plateau=%d' % (
        cid, arch, ok, w, d, cx, L, ccx, cu, row['crit_top_wires'], fam, st['plateau'].get(fam,0)))
    return row
