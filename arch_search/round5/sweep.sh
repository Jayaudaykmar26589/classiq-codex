#!/bin/bash
# $1 side, $2 worker id ; loops seeds: anneal (lanelev, free map) -> save best -> exhaustive polish
side=$1; wid=$2; cd /tmp/claude-0/-home-user-classiq-codex/9594a09f-2111-561b-9f50-1d65664744a3/scratchpad
for i in $(seq 1 200); do
  seed=$((wid*1000+i)); L=$(( 28 + (i % 3)*4 )); ml=$(( 4 + (i % 2) ))
  if [ "$side" = "y" ]; then nanc=3; else nanc=$(( 3 + (i % 3) )); fi
  timeout 1200 /tmp/claude-0/venv/bin/python rc/lev_save.py $side $nanc $L $ml $seed 700000 0 >> rc/sweep_${side}_${wid}.log 2>&1
  f=rc/levbest_${side}_${nanc}_${L}_${ml}_${seed}_0.json
  if [ "$side" = "y" ] && [ -f $f ]; then
    timeout 1500 /tmp/claude-0/venv/bin/python rc/polish_run.py $f 1400 >> rc/sweep_${side}_${wid}.log 2>&1
  fi
  if grep -q "RES 0 \|EXACT\|mis 0" rc/sweep_${side}_${wid}.log; then echo FOUND >> rc/sweep_${side}_${wid}.log; exit 0; fi
done
