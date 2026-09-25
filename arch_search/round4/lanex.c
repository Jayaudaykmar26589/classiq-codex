// lanex: SA over in-place lane programs + EXACT final AND level via quotient-space linear algebra.
// Points: up to 128 (two 64-bit words). Wires: W modifiable, R read-only (usable as controls / span).
// Program ops: kind 0: t ^= a ; kind 1: t ^= la & lb ; kind 2: nop.  (a,b may be read-only wires, index >= W)
// Goal: every target lies in span(final modifiable wires, read-only wires, 1).
// Input (stdin): NP W R K L MAXLEV iters restarts seed lam
//   K lines: target (hex lo hi) ; then W+R lines init tables (hex lo hi)
// Output: lines "RES wrong nand lev" then OP lines and FIN lines (final level gates) if exact.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#define MAXW 14
#define MAXOPS 64
#define MAXT 8
typedef struct { uint64_t w[2]; } TT;
typedef struct { int kind, t, a, na, b, nb; } Op;
static int NP, W, R, K, L, MAXLEV; static double lam;
static TT init[MAXW + 4], tgt[MAXT], ONE;
static uint64_t rng_s;
static inline uint64_t rnd() { rng_s ^= rng_s << 13; rng_s ^= rng_s >> 7; rng_s ^= rng_s << 17; return rng_s; }
static inline int ri(int n) { return (int)(rnd() % (uint64_t)n); }
static inline TT tx(TT a, TT b) { TT r = {{a.w[0] ^ b.w[0], a.w[1] ^ b.w[1]}}; return r; }
static inline TT ta(TT a, TT b) { TT r = {{a.w[0] & b.w[0], a.w[1] & b.w[1]}}; return r; }
static inline TT tn(TT a) { return tx(a, ONE); }
static inline int tz(TT a) { return !(a.w[0] | a.w[1]); }
static inline int pc(TT a) { return __builtin_popcountll(a.w[0]) + __builtin_popcountll(a.w[1]); }
static inline int lowbit(TT a) { return a.w[0] ? __builtin_ctzll(a.w[0]) : (a.w[1] ? 64 + __builtin_ctzll(a.w[1]) : -1); }
static inline int getb(TT a, int i) { return (a.w[i >> 6] >> (i & 63)) & 1; }
static int NT; // total wires W+R
static void run(Op *p, int n, TT *v, int *lv, int *nand) {
  for (int i = 0; i < NT; i++) { v[i] = init[i]; lv[i] = 0; } *nand = 0;
  for (int i = 0; i < n; i++) { Op o = p[i]; if (o.kind == 2) continue;
    TT A = o.na ? tn(v[o.a]) : v[o.a];
    if (o.kind == 0) { v[o.t] = tx(v[o.t], A); if (lv[o.a] > lv[o.t]) lv[o.t] = lv[o.a]; }
    else { TT B = o.nb ? tn(v[o.b]) : v[o.b]; v[o.t] = tx(v[o.t], ta(A, B)); (*nand)++;
      int m = (lv[o.a] > lv[o.b] ? lv[o.a] : lv[o.b]) + 1; if (lv[o.t] > m) m = lv[o.t]; lv[o.t] = m; } }
}
// ---- span distance (min Hamming over coset) ----
static int span_dist(TT *v, int n, TT t) {
  // gray code over n vectors + complement
  int best = 1 << 30; TT acc = {{0, 0}}; int N = 1 << n;
  for (int g = 0; g < N; g++) { if (g) acc = tx(acc, v[__builtin_ctz(g)]);
    TT d = tx(acc, t); int c0 = pc(d); int c1 = NP - c0; if (c0 < best) best = c0; if (c1 < best) best = c1; if (!best) return 0; }
  return best;
}
static double cost(Op *p, int n, int *wr, int *nandp, int *levp) {
  TT v[MAXW + 4]; int lv[MAXW + 4], na; run(p, n, v, lv, &na);
  int mx = 0; for (int i = 0; i < W; i++) if (lv[i] > mx) mx = lv[i];
  int tot = 0; for (int k = 0; k < K; k++) tot += span_dist(v, NT, tgt[k]);
  *wr = tot; *nandp = na; *levp = mx; int ex = mx > MAXLEV ? mx - MAXLEV : 0;
  return tot + lam * na + 10.0 * ex;
}
// ---- Gaussian basis (pivot = lowest set bit) ----
typedef struct { TT b[40]; int piv[40]; int n; } Basis;
static void bas_init(Basis *B) { B->n = 0; }
static TT reduce(const Basis *B, TT x) { for (int i = 0; i < B->n; i++) if (getb(x, B->piv[i])) x = tx(x, B->b[i]); return x; }
static int bas_add(Basis *B, TT x) { x = reduce(B, x); if (tz(x)) return 0; int p = lowbit(x);
  for (int i = 0; i < B->n; i++) if (getb(B->b[i], p)) B->b[i] = tx(B->b[i], x);
  B->b[B->n] = x; B->piv[B->n] = p; B->n++; return 1; }
// ---- exact final level ----
typedef struct { int t, a, b; } FG;
static FG finsol[4]; static int finn;
static int exact_final(TT *v, int *lv) {
  int idx[3];
  // m = 0
  { Basis B; bas_init(&B); for (int i = 0; i < NT; i++) bas_add(&B, v[i]); bas_add(&B, ONE);
    int ok = 1; for (int k = 0; k < K; k++) if (!tz(reduce(&B, tgt[k]))) { ok = 0; break; } if (ok) { finn = 0; return 1; } }
  for (int m = 1; m <= 3 && m <= W; m++) {
    for (int c = 0; c < (1 << W); c++) { if (__builtin_popcount(c) != m) continue;
      int q = 0; for (int i = 0; i < W; i++) if (c >> i & 1) idx[q++] = i;
      Basis B0; bas_init(&B0); for (int i = 0; i < NT; i++) if (!(i < W && (c >> i & 1))) bas_add(&B0, v[i]); bas_add(&B0, ONE);
      Basis BT = B0; int d = 0; for (int k = 0; k < K; k++) d += bas_add(&BT, tgt[k]);
      if (d != m) continue;
      // candidates per target wire: q = v_t ^ (a&b), need reduce(B0,q)!=0 and reduce(BT,q)==0
      static TT cq[3][200]; static int ca[3][200], cb[3][200]; int cn[3] = {0, 0, 0};
      for (int s = 0; s < m; s++) { int t = idx[s];
        // no-gate option
        TT q0 = reduce(&B0, v[t]); if (!tz(q0) && tz(reduce(&BT, v[t]))) { cq[s][cn[s]] = q0; ca[s][cn[s]] = -1; cb[s][cn[s]] = -1; cn[s]++; }
        for (int a = 0; a < NT; a++) { if (a < W && (c >> a & 1)) continue; if (lv[a] > MAXLEV - 1) continue;
          for (int b = a + 1; b < NT; b++) { if (b < W && (c >> b & 1)) continue; if (lv[b] > MAXLEV - 1) continue;
            TT qq = tx(v[t], ta(v[a], v[b]));
            if (tz(reduce(&BT, qq))) { TT r0 = reduce(&B0, qq); if (!tz(r0) && cn[s] < 200) { cq[s][cn[s]] = r0; ca[s][cn[s]] = a; cb[s][cn[s]] = b; cn[s]++; } } } }
        if (!cn[s]) goto next; }
      // choose one per target, independent in quotient
      if (m == 1) { finsol[0] = (FG){idx[0], ca[0][0], cb[0][0]}; finn = 1; return 1; }
      for (int i0 = 0; i0 < cn[0]; i0++) for (int i1 = 0; i1 < cn[1]; i1++) {
        Basis Q; bas_init(&Q); bas_add(&Q, cq[0][i0]); if (!bas_add(&Q, cq[1][i1])) continue;
        if (m == 2) { finsol[0] = (FG){idx[0], ca[0][i0], cb[0][i0]}; finsol[1] = (FG){idx[1], ca[1][i1], cb[1][i1]}; finn = 2; return 1; }
        for (int i2 = 0; i2 < cn[2]; i2++) { Basis Q2 = Q; if (!bas_add(&Q2, cq[2][i2])) continue;
          finsol[0] = (FG){idx[0], ca[0][i0], cb[0][i0]}; finsol[1] = (FG){idx[1], ca[1][i1], cb[1][i1]}; finsol[2] = (FG){idx[2], ca[2][i2], cb[2][i2]}; finn = 3; return 1; } }
      next:;
    } }
  return 0;
}
static void rand_op(Op *o) {
  int r = ri(8); o->kind = r < 4 ? 1 : (r < 7 ? 0 : 2);
  o->t = ri(W); do o->a = ri(NT); while (o->a == o->t); o->na = ri(2);
  if (o->kind == 1) { do o->b = ri(NT); while (o->b == o->t || o->b == o->a); o->nb = ri(2); } else { o->b = 0; o->nb = 0; }
}
int main() {
  int iters, restarts; unsigned long long seed;
  if (scanf("%d %d %d %d %d %d %d %d %llu %lf", &NP, &W, &R, &K, &L, &MAXLEV, &iters, &restarts, &seed, &lam) != 10) return 1;
  NT = W + R; ONE.w[0] = NP >= 64 ? ~0ULL : ((1ULL << NP) - 1); ONE.w[1] = NP > 64 ? (NP >= 128 ? ~0ULL : ((1ULL << (NP - 64)) - 1)) : 0;
  for (int k = 0; k < K; k++) { unsigned long long a, b; scanf("%llx %llx", &a, &b); tgt[k].w[0] = a; tgt[k].w[1] = b; }
  for (int i = 0; i < NT; i++) { unsigned long long a, b; scanf("%llx %llx", &a, &b); init[i].w[0] = a; init[i].w[1] = b; }
  rng_s = seed * 2654435761ULL + 12345; if (!rng_s) rng_s = 1;
  Op best[MAXOPS]; double bestc = 1e18; int bestwr = 1 << 30, bestna = 0, bestlev = 0;
  long checks = 0;
  for (int rs = 0; rs < restarts; rs++) {
    Op cur[MAXOPS]; for (int i = 0; i < L; i++) rand_op(&cur[i]);
    int wr, na, lev; double c = cost(cur, L, &wr, &na, &lev);
    double T0 = 2.0, T1 = 0.05;
    for (int it = 0; it < iters; it++) {
      double T = T0 * pow(T1 / T0, (double)it / iters);
      Op save[2]; int i1 = ri(L), i2 = -1; save[0] = cur[i1];
      int mv = ri(10);
      if (mv < 6) rand_op(&cur[i1]);
      else if (mv < 8) { i2 = ri(L); save[1] = cur[i2]; Op t = cur[i1]; cur[i1] = cur[i2]; cur[i2] = t; }
      else { // tweak a field
        Op *o = &cur[i1]; int f = ri(3); if (o->kind == 2) rand_op(o);
        else if (f == 0) { o->na ^= 1; } else if (f == 1 && o->kind == 1) o->nb ^= 1; else { int a; do a = ri(NT); while (a == o->t || (o->kind == 1 && a == o->b)); o->a = a; } }
      int nwr, nna, nlev; double nc = cost(cur, L, &nwr, &nna, &nlev);
      if (nc <= c || exp((c - nc) / T) > (double)(rnd() % 1000000) / 1e6) { c = nc; wr = nwr; na = nna; lev = nlev;
        if ((it & 63) == 0 || wr <= 12) { // exact final-level check on prefixes
          for (int cut = 0; cut <= 4; cut++) { TT v[MAXW + 4]; int lv[MAXW + 4], nn; run(cur, L - cut, v, lv, &nn); int mx = 0; for (int i = 0; i < W; i++) if (lv[i] > mx) mx = lv[i];
            if (mx > MAXLEV) continue; checks++;
            if (exact_final(v, lv)) {
              printf("RES 0 %d %d checks %ld restart %d it %d cut %d\n", nn + finn, MAXLEV, checks, rs, it, cut);
              for (int i = 0; i < L - cut; i++) printf("OP %d %d %d %d %d %d\n", cur[i].kind, cur[i].t, cur[i].a, cur[i].na, cur[i].b, cur[i].nb);
              for (int i = 0; i < finn; i++) printf("FIN %d %d %d\n", finsol[i].t, finsol[i].a, finsol[i].b);
              fflush(stdout); return 0; } } }
      } else { if (i2 >= 0) cur[i2] = save[1]; cur[i1] = save[0]; }
      if (c < bestc) { bestc = c; bestwr = wr; bestna = na; bestlev = lev; memcpy(best, cur, sizeof(Op) * L); }
    }
  }
  printf("RES %d %d %d checks %ld\n", bestwr, bestna, bestlev, checks);
  for (int i = 0; i < L; i++) printf("OP %d %d %d %d %d %d\n", best[i].kind, best[i].t, best[i].a, best[i].na, best[i].b, best[i].nb);
  return 0;
}
