// polish: exhaustive 1-2 op edits of an in-place lane program to reach level consistency (free map).
// stdin: NP W R L cw0 cw1 cw2 ; want[NP] ; init tables W+R (hex lo hi) ; L ops (kind t a na b nb)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef struct { uint64_t w[2]; } TT;
typedef struct { int kind, t, a, na, b, nb; } Op;
static int NP, W, R, L, NT, NB, cw[8], want[128]; static TT init[20], ONE;
static inline int getb(TT a, int i) { return (a.w[i >> 6] >> (i & 63)) & 1; }
static void apply(TT *v, Op o) { if (o.kind == 2) return; TT A = v[o.a]; if (o.na) { A.w[0] ^= ONE.w[0]; A.w[1] ^= ONE.w[1]; }
  if (o.kind == 0) { v[o.t].w[0] ^= A.w[0]; v[o.t].w[1] ^= A.w[1]; }
  else { TT B = v[o.b]; if (o.nb) { B.w[0] ^= ONE.w[0]; B.w[1] ^= ONE.w[1]; } v[o.t].w[0] ^= A.w[0] & B.w[0]; v[o.t].w[1] ^= A.w[1] & B.w[1]; } }
static int mis(TT *v) { static int cnt[256][16]; memset(cnt, 0, sizeof cnt); int nk[256] = {0};
  for (int p = 0; p < NP; p++) { int k = 0; for (int b = 0; b < NB; b++) k |= getb(v[cw[b]], p) << b; cnt[k][want[p]]++; nk[k]++; }
  int c = 0; for (int k = 0; k < (1 << NB); k++) { int m = 0; for (int l = 0; l < 16; l++) if (cnt[k][l] > m) m = cnt[k][l]; c += nk[k] - m; } return c; }
static Op ops[64], cand[4096]; static int NC;
static void run_prefix(TT *v, int upto) { for (int i = 0; i < NT; i++) v[i] = init[i]; for (int i = 0; i < upto; i++) apply(v, ops[i]); }
int main() {
  if (scanf("%d %d %d %d %d", &NP, &W, &R, &L, &NB) != 5) return 1; for (int b = 0; b < NB; b++) scanf("%d", &cw[b]); NT = W + R;
  ONE.w[0] = NP >= 64 ? ~0ULL : ((1ULL << NP) - 1); ONE.w[1] = NP > 64 ? (NP >= 128 ? ~0ULL : ((1ULL << (NP - 64)) - 1)) : 0;
  for (int p = 0; p < NP; p++) scanf("%d", &want[p]);
  for (int i = 0; i < NT; i++) { unsigned long long a, b; scanf("%llx %llx", &a, &b); init[i].w[0] = a; init[i].w[1] = b; }
  for (int i = 0; i < L; i++) scanf("%d %d %d %d %d %d", &ops[i].kind, &ops[i].t, &ops[i].a, &ops[i].na, &ops[i].b, &ops[i].nb);
  NC = 0;
  for (int t = 0; t < W; t++) for (int a = 0; a < NT; a++) { if (a == t) continue;
    for (int na = 0; na < 2; na++) cand[NC++] = (Op){0, t, a, na, 0, 0};
    for (int b = a + 1; b < NT; b++) { if (b == t) continue; for (int na = 0; na < 2; na++) for (int nb = 0; nb < 2; nb++) cand[NC++] = (Op){1, t, a, na, b, nb}; } }
  TT v[20], v2[20], v3[20]; run_prefix(v, L); int base = mis(v); printf("base mis %d, candidates %d\n", base, NC); fflush(stdout);
  int best = base;
  // single insertion at position pos / single replacement
  for (int pos = 0; pos <= L; pos++) { TT pre[20]; run_prefix(pre, pos);
    for (int c = 0; c < NC; c++) { for (int m = 0; m < 2; m++) { if (m == 1 && pos == L) continue;
        memcpy(v2, pre, sizeof(TT) * NT); apply(v2, cand[c]); for (int i = pos + m; i < L; i++) apply(v2, ops[i]);
        int s = mis(v2); if (s < best) { best = s; printf("%s at %d: op %d %d %d %d %d %d -> mis %d\n", m ? "REPLACE" : "INSERT", pos, cand[c].kind, cand[c].t, cand[c].a, cand[c].na, cand[c].b, cand[c].nb, s); fflush(stdout); }
        if (s == 0) return 0; } } }
  // append pairs
  for (int c1 = 0; c1 < NC; c1++) { memcpy(v2, v, sizeof(TT) * NT); apply(v2, cand[c1]);
    for (int c2 = 0; c2 < NC; c2++) { memcpy(v3, v2, sizeof(TT) * NT); apply(v3, cand[c2]); int s = mis(v3);
      if (s < best) { best = s; printf("APPEND2 %d %d %d %d %d %d | %d %d %d %d %d %d -> mis %d\n", cand[c1].kind, cand[c1].t, cand[c1].a, cand[c1].na, cand[c1].b, cand[c1].nb, cand[c2].kind, cand[c2].t, cand[c2].a, cand[c2].na, cand[c2].b, cand[c2].nb, s); fflush(stdout); }
      if (s == 0) return 0; } }
  // insert pairs at arbitrary positions (pos1 <= pos2)
  for (int p1 = 0; p1 <= L; p1++) { TT pre[20]; run_prefix(pre, p1);
    for (int c1 = 0; c1 < NC; c1++) { TT a1[20]; memcpy(a1, pre, sizeof(TT) * NT); apply(a1, cand[c1]);
      for (int p2 = p1; p2 <= L; p2++) { TT a2[20]; memcpy(a2, a1, sizeof(TT) * NT); for (int i = p1; i < p2; i++) apply(a2, ops[i]);
        for (int c2 = 0; c2 < NC; c2++) { memcpy(v3, a2, sizeof(TT) * NT); apply(v3, cand[c2]); for (int i = p2; i < L; i++) apply(v3, ops[i]);
          int s = mis(v3); if (s < best) { best = s; printf("INSERT2 at %d,%d -> mis %d\n", p1, p2, s); fflush(stdout); } if (s == 0) { printf("EXACT\n"); return 0; } } } } }
  printf("final best %d\n", best); return 0; }
