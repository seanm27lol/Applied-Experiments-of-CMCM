# Part III: witness supervision vs witness recoverability

Tests whether the Part I null (diff supervision adds nothing over pairing)
was a property of the domain's search/verification gap. Lean tactic steps
are the wide-gap domain: checking a tactic is cheap, reconstructing it from
goal states is search. See PREREGISTRATION.md — commit it before running.

Pipeline (run on the DGX Spark, inside the venv):
    pip install datasets transformers torch scipy
    python3 prep_data.py                # ~10 min, downloads leandojo steps
    python3 train.py --arm pw_trace     # repeat for pw_pair, pw_endpoint
    python3 eval.py  --arm pw_trace     # repeat for all arms
    python3 stats.py                    # P1/P2 verdicts

Smoke test the plumbing first (CPU-safe, minutes):
    python3 prep_data.py --n_steps 500 --n_eval 20 --budget 300000
    python3 train.py --arm pw_trace --smoke --model sshleifer/tiny-gpt2
    python3 eval.py --arm pw_trace --n 5
