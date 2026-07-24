# Part IV: does witness information predict the supervision gap?

Parts I and III found opposite results for trace-versus-endpoint
supervision in two domains. This part tests whether a computable quantity
explains the difference: the fiber, the number of witnesses sharing an
endpoint pair.

Commit PREREGISTRATION.md before running anything.

## Files

  WitnessRecoverability.lean  recoverability as faithfulness of the
                              forgetful map; kernel-checked, no axioms
  fiber.py                    exact fiber statistics per operation set
  gen_synth.py                corpora for one condition, four arms
  train_synth.py              two-stage training, one arm
  eval_synth.py               predict witness from endpoints
  stats_fiber.py              the gap-versus-log-fiber regression

## Check the formal layer

    lean WitnessRecoverability.lean

Prints fiber counts for small systems and accepts every theorem. The
#print axioms lines confirm no sorries and no custom axioms.

## Check the fiber numbers

    python3 fiber.py --L 6

Exhaustive, not sampled: enumerates all 8^6 witnesses per condition.

## Run the experiment

    pip install datasets transformers accelerate torch scipy numpy

    for o in readable free q25 q50 q75 abelian; do
      python3 gen_synth.py --opset $o --L 6
      for a in sy_trace sy_pair sy_endpoint sy_shuffle; do
        python3 train_synth.py --opset $o --arm $a
        python3 eval_synth.py  --opset $o --arm $a
      done
    done
    python3 stats_fiber.py

Twenty-four training runs. Budget roughly a night on one GPU.

Smoke test first (minutes, CPU-safe):

    python3 gen_synth.py --opset readable --L 6 --n 400 --n_eval 8 --budget 60000
    python3 train_synth.py --opset readable --arm sy_trace --smoke \
        --model sshleifer/tiny-gpt2 --bs 2 --seq 128
    python3 eval_synth.py --opset readable --arm sy_trace --n 4
    rm -rf data ckpt results

## Reading the output

stats_fiber.py prints one row per condition, then the P4a regression of
gap on log2 fiber, then the P4b comparison between `readable` and `free`,
which share a fiber size of 1.00 but differ in whether the witness can be
computed from the endpoints.
