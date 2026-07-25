# Part V: is the trace advantage a data-efficiency effect?

Holds stage 1 fixed and varies the stage-2 budget, on the Part III data.
A gap that decays to zero means stage-2 examples can buy what stage-1
trace exposure provides. A gap that persists means they cannot.

Commit PREREGISTRATION.md before running.

## Precondition

    wc -l data/stage2_pool.jsonl

Must be at least 4000. If smaller, the N=4000 point is capped and the
prereg needs a dated note before running.

## Setup

Run from the proof_witness directory, which already holds data/ from
Part III. Copy these four files in, or symlink data/ here.

    ls data/pw_trace_train.jsonl data/stage2_pool.jsonl data/eval.jsonl

## Run

    source ../.venv/bin/activate

    # stage 1 once per arm (the expensive part, about an hour each)
    python3 train_stage1.py --arm pw_trace
    python3 train_stage1.py --arm pw_pair

    # then each budget is a short fine-tune plus an eval
    for n in 125 250 500 1000 2000 4000; do
      for a in pw_trace pw_pair; do
        python3 train_stage2.py --arm $a --n $n && \
        python3 eval_budget.py --arm $a --n $n
      done
    done
    python3 stats_budget.py

Two long runs plus twelve short ones. Roughly three to four hours total,
most of it the two stage-1 runs and the twelve evals.

## Smoke test first

    python3 train_stage1.py --arm pw_trace --smoke --model sshleifer/tiny-gpt2 --bs 2 --seq 256
    python3 train_stage2.py --arm pw_trace --n 32 --smoke --bs 2 --seq 256
    python3 eval_budget.py --arm pw_trace --n 32 --n_eval 4
    rm -rf ckpt ckpt_s1 results

## Reading the output

stats_budget.py prints the gap at each budget, then the P5a regression of
gap on log2 N, then the P5b value at the largest budget. The N=2000 row is
the P5c anchor and should reproduce Part III's +0.054 at seed 0.
