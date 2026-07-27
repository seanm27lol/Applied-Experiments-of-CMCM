#!/bin/bash
# run_all.sh: the registered 24-run queue with the A1 abort gate.
# Per PREREGISTRATION.md: if the A1 anchor fails on `readable`, stop
# rather than spend the remaining hours. The search evaluation follows
# the main queue (no new training). Logs to run_all.log.
set -uo pipefail
cd "$(dirname "$0")"
PY=../.venv/bin/python
LOG=run_all.log
export HF_HUB_OFFLINE=1
: > "$LOG"

systems="readable free q25 q50 q75 abelian"
arms="sc_pair sc_cost sc_costd sc_counts"

for s in $systems; do
  echo "[$(date +%F' '%T)] gen $s" | tee -a "$LOG"
  $PY gen_cost.py --system "$s" >> "$LOG" 2>&1 \
    || { echo "GEN FAIL $s" | tee -a "$LOG"; exit 1; }
  for a in $arms; do
    echo "[$(date +%F' '%T)] train $s $a" | tee -a "$LOG"
    $PY train_cost.py --system "$s" --arm "$a" >> "$LOG" 2>&1 \
      || { echo "TRAIN FAIL $s $a" | tee -a "$LOG"; exit 1; }
    $PY eval_cost.py --system "$s" --arm "$a" >> "$LOG" 2>&1 \
      || { echo "EVAL FAIL $s $a" | tee -a "$LOG"; exit 1; }
  done
  if [ "$s" = readable ]; then
    $PY stats_cost.py >> "$LOG" 2>&1
    if grep -q "A1 anchor.*PASS" "$LOG"; then
      echo "[$(date +%F' '%T)] A1 anchor PASS; continuing" | tee -a "$LOG"
    else
      echo "[$(date +%F' '%T)] A1 anchor FAIL; stop per registration" \
        | tee -a "$LOG"
      exit 2
    fi
  fi
done

echo "[$(date +%F' '%T)] main queue done; search evaluation" | tee -a "$LOG"
for s in q50 q75 abelian; do
  $PY search_cost.py --system "$s" --arm sc_cost >> "$LOG" 2>&1 \
    || echo "SEARCH FAIL $s" | tee -a "$LOG"
done
$PY stats_cost.py >> "$LOG" 2>&1
echo "[$(date +%F' '%T)] ALL DONE" | tee -a "$LOG"
