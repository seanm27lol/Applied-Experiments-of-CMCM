"""train_stage2.py: fine-tune a saved stage-1 checkpoint on N stage-2
examples, then write the model. Part V's dial is N.

Stage 2 is identical in content for every arm at a given N and seed: the
same examples in the same order, drawn from the shared stage2_pool that
Part III already built. Only the stage-1 checkpoint differs.

Usage: python3 train_stage2.py --arm pw_trace --n 500 [--seed 0]
Writes: ckpt/<arm>_n<N>[_s<seed>]/
"""
import argparse, json, os, random

import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          DataCollatorForLanguageModeling, Trainer,
                          TrainingArguments)

B, T, A, E = "<|STATE_BEFORE|>", "<|TACTIC|>", "<|STATE_AFTER|>", "<|END|>"
MAX_STATE = 1200


def clip(s):
    s = (s or "").strip()
    return s[-MAX_STATE:] if len(s) > MAX_STATE else s


def detag(s):
    import re
    return re.sub(r"</?a>", "", s or "")


def stage2_doc(ex):
    return (f"{B}\n{clip(ex['state'])}\n{A}\n{clip(ex['target_state'])}\n"
            f"{T}\n{detag(ex['tactic']).strip()}\n{E}\n")


def assert_finite(model, where):
    bad = [n for n, p in model.named_parameters()
           if not torch.isfinite(p).all()]
    if bad:
        raise RuntimeError(f"non-finite weights after {where}: {bad[:5]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--n", type=int, required=True,
                    help="stage-2 example budget: the Part V dial")
    ap.add_argument("--seq", type=int, default=768)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--lr2", type=float, default=2e-5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    suf = "" if args.seed == 0 else f"_s{args.seed}"
    ck = f"ckpt_s1/{args.arm}{suf}"
    if not os.path.isdir(ck):
        raise SystemExit(f"missing stage-1 checkpoint {ck}; "
                         f"run train_stage1.py --arm {args.arm} first")

    tok = AutoTokenizer.from_pretrained(ck)
    model = AutoModelForCausalLM.from_pretrained(ck, dtype=torch.float32)

    # the stage-2 sample depends ONLY on the seed and N, never on the arm,
    # so every arm at a given (N, seed) sees identical examples in identical
    # order. Nested draws: the N=250 set is a prefix of the N=500 set.
    pool = [json.loads(l) for l in open("data/stage2_pool.jsonl")]
    order = list(range(len(pool)))
    random.Random(1 + args.seed).shuffle(order)
    take = order[: min(args.n, len(pool))]
    if len(take) < args.n:
        print(f"  WARNING: pool has {len(pool)} examples, "
              f"requested {args.n}; using {len(take)}")
    rows = [{"text": stage2_doc(pool[i])} for i in take]
    if args.smoke:
        rows = rows[:16]

    ds = Dataset.from_list(rows)
    ds = ds.map(lambda b: tok(b["text"], truncation=True,
                              max_length=args.seq),
                batched=True, remove_columns=ds.column_names)
    targs = TrainingArguments(
        output_dir=f"ckpt/tmp_{args.arm}_{args.n}", num_train_epochs=1,
        learning_rate=args.lr2, per_device_train_batch_size=args.bs,
        gradient_accumulation_steps=4, bf16=False, fp16=False,
        warmup_ratio=0.03, max_grad_norm=1.0, logging_steps=25,
        save_strategy="no", report_to=[])
    Trainer(model=model, args=targs, train_dataset=ds,
            data_collator=DataCollatorForLanguageModeling(tok, mlm=False)
            ).train()
    assert_finite(model, "stage 2")

    out = f"ckpt/{args.arm}_n{args.n}{suf}"
    model.save_pretrained(out)
    tok.save_pretrained(out)
    print(f"saved {out}  (stage-2 examples: {len(rows)})")


if __name__ == "__main__":
    main()
