# The cost channel: an intermediate supervision rung

Idea credit: Sebastien Seboih. Commit PREREGISTRATION.md before running.

## Check the theory first (no GPU, seconds)

    python3 -c "import json;print(open('ceilings.json').read())"

## Run (24 runs, roughly 6-8 hours)

    source ../.venv/bin/activate
    for s in readable free q25 q50 q75 abelian; do
      python3 gen_cost.py --system $s
      for a in sc_pair sc_cost sc_costd sc_counts; do
        python3 train_cost.py --system $s --arm $a && \
        python3 eval_cost.py  --system $s --arm $a
      done
    done
    python3 stats_cost.py

## Smoke test first (minutes)

    python3 gen_cost.py --system readable --n 300 --n_eval 20
    python3 train_cost.py --system readable --arm sc_cost --smoke \
        --model sshleifer/tiny-gpt2 --bs 4 --seq 128
    python3 eval_cost.py --system readable --arm sc_cost --n 4
    rm -rf data ckpt results

## Search evaluation (after the main run, no new training)

    for s in q50 q75 abelian; do
      python3 search_cost.py --system $s --arm sc_cost
    done

Asks the trained model for progressively cheaper paths and verifies each
one by running it forward. Skips items whose endpoint admits only one
achievable cost. The impossible rung is the control: a model scoring
above 0.05 there is ignoring the cost field.

## Abort check

Run `python3 stats_cost.py` as soon as `readable` finishes all three
arms. A1 requires all four arms at 0.90 or better on that system. It is a
copy task; if it fails, stop rather than spend the remaining hours.
