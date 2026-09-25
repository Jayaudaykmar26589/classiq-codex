# Classiq Qmod models of the new exact formulations

These are high-level Qmod models of the logo oracle, meant for Classiq's synthesis engine. Each model is checked classically on all 4096 pixels (`build_models.py`). They are **not synthesized yet**: this repository's cloud environment blocks every Classiq host.

| Model | Formulation | Check |
|---|---|---|
| `staircase_two_lut` | The row swap y5 ^= y4·y3·y2 is folded into the tables. The logo becomes `[LY0[y] <= LX0[x]] XOR [LY1[y] <= LX1[x]]`: one row-level vs column-level comparison per half, using quantum-indexed lookups. | 0/4096 mismatches; halves disjoint |
| `staircase_or_lut` | The same comparator written as one OR predicate, so the engine can share the lookups. | 0/4096 |
| `xor_rectangles` | 17 overlapping rectangles combined by XOR (the minimum allowed by the 68 corners), against the baseline's 18 disjoint ones. | 0/4096 |

## Running

1. Install and sign in once: `pip install classiq==1.29.1`, then `python -c "import classiq; classiq.authenticate()"`. Sign-in uses a one-time browser confirmation, not a password.
2. Rebuild the models: `python build_models.py`
3. Sweep seeds: `python synth_sweep.py --seeds 8` (other options: `--transpile intensive|custom`, and model names).

The script repeats the baseline notebook's pipeline:

- synthesize with depth optimization and max width 18;
- remove the two harness `hadamard_transform` calls;
- transpile to u3/cx;
- compute metrics with `qasm_metrics`;
- run the exact all-4096 check from `../arch_search/sparse_verify.py`.

Results go to `sweep_results/`, and the best verified candidate is printed at the end.
