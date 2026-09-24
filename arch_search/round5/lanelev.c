// lanelev: SA over in-place lane programs; objective = LEVEL CONSISTENCY of designated code wires.
// Points up to 128. W modifiable wires (first ones), R read-only. Code wires = indices cw[0..NB-1] (modifiable).
// Each point p has a wanted level want[p] (0..15). Code value k=(bits of code wires at p).
// Cost = sum_k (n_k - agree_k) where agree_k = #points with want==L[k] (fixed map) or max level count (free map).
// Input: NP W R NB L MAXLEV iters restarts seed lam fixed ; cw[NB] ; want[NP] ; (if fixed) L[2^NB] ; init tables W+R (hex lo hi)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#define MAXW 16
#define MAXOPS 80
typedef struct { uint64_t w[2]; } TT;
typedef struct { int kind, t, a, na, b, nb; } Op;
static int NP, W, R, NB, L, MAXLEV, FIXED, NT; static double lam;
static int cw[8], want[128], Lmap[64]; static TT init[MAXW], ONE;
static uint64_t rng_s;
static inline uint64_t rnd() { rng_s ^= rng_s << 13; rng_s ^= rng_s >> 7; rng_s ^= rng_s << 17; return rng_s; }
static inline int ri(int n) { return (int)(rnd() % (uint64_t)n); }
static inline int getb(TT a, int i) { return (a.w[i >> 6] >> (i & 63)) & 1; }
static void run(Op *p, int n, TT *v, int *lv, int *nand) {
  for (int i = 0; i < NT; i++) { v[i] = init[i]; lv[i] = 0; } *nand = 0;
  for (int i = 0; i < n; i++) { Op o = p[i]; if (o.kind == 2) continue;
    TT A = v[o.a]; if (o.na) { A.w[0] ^= ONE.w[0]; A.w[1] ^= ONE.w[1]; }
    if (o.kind == 0) { v[o.t].w[0] ^= A.w[0]; v[o.t].w[1] ^= A.w[1]; if (lv[o.a] > lv[o.t]) lv[o.t] = lv[o.a]; }
    else { TT B = v[o.b]; if (o.nb) { B.w[0] ^= ONE.w[0]; B.w[1] ^= ONE.w[1]; }
      v[o.t].w[0] ^= A.w[0] & B.w[0]; v[o.t].w[1] ^= A.w[1] & B.w[1]; (*nand)++;
      int m = (lv[o.a] > lv[o.b] ? lv[o.a] : lv[o.b]) + 1; if (lv[o.t] > m) m = lv[o.t]; lv[o.t] = m; } }
}
static int mis(TT *v) {
  int cnt[64][16]; memset(cnt, 0, sizeof cnt); int nk[64]; memset(nk, 0, sizeof nk);
  for (int p = 0; p < NP; p++) { int k = 0; for (int b = 0; b < NB; b++) k |= getb(v[cw[b]], p) << b; cnt[k][want[p]]++; nk[k]++; }
  int c = 0;
  for (int k = 0; k < (1 << NB); k++) { if (!nk[k]) continue;
    if (FIXED) c += nk[k] - cnt[k][Lmap[k]];
    else { int m = 0; for (int l = 0; l < 16; l++) if (cnt[k][l] > m) m = cnt[k][l]; c += nk[k] - m; } }
  return c;
}
static double cost(Op *p, int *wr, int *na, int *lev) {
  TT v[MAXW]; int lv[MAXW]; run(p, L, v, lv, na); int mx = 0; for (int i = 0; i < W; i++) if (lv[i] > mx) mx = lv[i];
  *lev = mx; *wr = mis(v); int ex = mx > MAXLEV ? mx - MAXLEV : 0; return *wr + lam * (*na) + 10.0 * ex;
}
static void rand_op(Op *o) { int r = ri(8); o->kind = r < 4 ? 1 : (r < 7 ? 0 : 2);
  o->t = ri(W); do o->a = ri(NT); while (o->a == o->t); o->na = ri(2);
  if (o->kind == 1) { do o->b = ri(NT); while (o->b == o->t || o->b == o->a); o->nb = ri(2); } else { o->b = 0; o->nb = 0; } }
int main() {
  int iters, restarts; unsigned long long seed;
  if (scanf("%d %d %d %d %d %d %d %d %llu %lf %d", &NP, &W, &R, &NB, &L, &MAXLEV, &iters, &restarts, &seed, &lam, &FIXED) != 11) return 1;
  NT = W + R; ONE.w[0] = NP >= 64 ? ~0ULL : ((1ULL << NP) - 1); ONE.w[1] = NP > 64 ? (NP >= 128 ? ~0ULL : ((1ULL << (NP - 64)) - 1)) : 0;
  for (int b = 0; b < NB; b++) if (scanf("%d", &cw[b]) != 1) return 2;
  for (int p = 0; p < NP; p++) if (scanf("%d", &want[p]) != 1) return 3;
  if (FIXED) for (int k = 0; k < (1 << NB); k++) if (scanf("%d", &Lmap[k]) != 1) return 4;
  for (int i = 0; i < NT; i++) { unsigned long long a, b; if (scanf("%llx %llx", &a, &b) != 2) return 5; init[i].w[0] = a; init[i].w[1] = b; }
  rng_s = seed * 2654435761ULL + 99; if (!rng_s) rng_s = 1;
  Op best[MAXOPS]; double bestc = 1e18; int bw = 1 << 30, bn = 0, bl = 0;
  for (int rs = 0; rs < restarts; rs++) {
    Op cur[MAXOPS]; for (int i = 0; i < L; i++) rand_op(&cur[i]);
    int wr, na, lev; double c = cost(cur, &wr, &na, &lev);
    for (int it = 0; it < iters; it++) {
      double T = 3.0 * pow(0.03 / 3.0, (double)it / iters);
      int i1 = ri(L), i2 = -1; Op s1 = cur[i1], s2; int mv = ri(10);
      if (mv < 6) rand_op(&cur[i1]);
      else if (mv < 8) { i2 = ri(L); s2 = cur[i2]; cur[i1] = s2; cur[i2] = s1; }
      else { Op *o = &cur[i1]; if (o->kind == 2) rand_op(o); else { int f = ri(3); if (f == 0) o->na ^= 1; else if (f == 1 && o->kind == 1) o->nb ^= 1;
        else { int a; do a = ri(NT); while (a == o->t || (o->kind == 1 && a == o->b)); o->a = a; } } }
      int nw, nn, nl; double nc = cost(cur, &nw, &nn, &nl);
      if (nc <= c || exp((c - nc) / T) > (double)(rnd() % 1000000) / 1e6) { c = nc; wr = nw; na = nn; lev = nl; }
      else { if (i2 >= 0) cur[i2] = s2; cur[i1] = s1; }
      if (c < bestc) { bestc = c; bw = wr; bn = na; bl = lev; memcpy(best, cur, sizeof(Op) * L); }
      if (bw == 0 && bl <= MAXLEV) break;
    }
    if (bw == 0 && bl <= MAXLEV) break;
  }
  printf("RES %d %d %d\n", bw, bn, bl);
  for (int i = 0; i < L; i++) printf("OP %d %d %d %d %d %d\n", best[i].kind, best[i].t, best[i].a, best[i].na, best[i].b, best[i].nb);
  return 0;
}
