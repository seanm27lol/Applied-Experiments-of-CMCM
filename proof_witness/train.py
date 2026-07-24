"""train.py: two-stage training for one arm.

Stage 1: causal LM on the arm's corpus (this is where the arms differ).
Stage 2: identical small finetune for every arm on the eval format
         STATE_BEFORE + STATE_AFTER -> TACTIC, using the SAME stage-2
         example set (built from train_pool triples, disjoint from eval).

Usage: python3 train.py --arm pw_trace [--model EleutherAI/pythia-160m]
                        [--stage2_n 2000] [--epochs 1] [--seq 768]
Writes: ckpt/<arm>/
"""
import argparse, re, json, os, random

import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          DataCollatorForLanguageModeling, Trainer,
                          TrainingArguments)

B, T, A, E = "<|STATE_BEFORE|>", "<|TACTIC|>", "<|STATE_AFTER|>", "<|END|>"
MAX_STATE = 1200


def detag(s):
    return re.sub(r"</?a>", "", s or "")


def clip(s):
    s = (s or "").strip()
    return s[-MAX_STATE:] if len(s) > MAX_STATE else s


def stage2_doc(ex):
    return (f"{B}\n{clip(ex['state'])}\n{A}\n{clip(ex['target_state'])}\n"
            f"{T}\n{ex['tactic'].strip()}\n{E}\n")


def tokenize(ds, tok, seq):
    def fn(b):
        out = tok(b["text"], truncation=True, max_length=seq)
        return out
    return ds.map(fn, batched=True, remove_columns=ds.column_names)


def assert_finite(model, where):
    bad = [n for n, p in model.named_parameters()
           if not torch.isfinite(p).all()]
    if bad:
        raise RuntimeError(
            f"non-finite weights after {where}: {bad[:5]} "
            f"({len(bad)} tensors). Lower --lr1/--lr2 and rerun.")


def run(model, tok, ds, outdir, epochs, lr, bs):
    args = TrainingArguments(
        output_dir=outdir, num_train_epochs=epochs, learning_rate=lr,
        per_device_train_batch_size=bs, gradient_accumulation_steps=4,
        bf16=False, fp16=False, logging_steps=50,
        warmup_ratio=0.03, max_grad_norm=1.0,
        save_strategy="no", report_to=[])
    Trainer(model=model, args=args, train_dataset=ds,
            data_collator=DataCollatorForLanguageModeling(tok, mlm=False)
            ).train()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["pw_trace", "pw_pair", "pw_endpoint"])
    ap.add_argument("--model", default="EleutherAI/pythia-160m")
    ap.add_argument("--stage2_n", type=int, default=2000)
    ap.add_argument("--epochs", type=float, default=1)
    ap.add_argument("--seq", type=int, default=768)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--lr1", type=float, default=5e-5)
    ap.add_argument("--lr2", type=float, default=2e-5)
    ap.add_argument("--smoke", action="store_true",
                    help="tiny run to validate plumbing")
    args = ap.parse_args()
    torch.manual_seed(0)

    tok = AutoTokenizer.from_pretrained(args.model)
    tok.add_special_tokens({"additional_special_tokens": [B, T, A, E]})
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model)
    model.resize_token_embeddings(len(tok), mean_resizing=False)

    s1 = [json.loads(l) for l in open(f"data/{args.arm}_train.jsonl")]
    s1 = [d for d in s1 if len(d["text"].strip()) > 20]
    if args.smoke:
        s1 = s1[:32]
    run(model, tok, tokenize(Dataset.from_list(s1), tok, args.seq),
        f"ckpt/{args.arm}_s1", args.epochs if not args.smoke else 1,
        args.lr1, args.bs)
    assert_finite(model, "stage 1")

    # stage 2: same examples for every arm (seeded from the trace corpus's
    # source triples via a fixed file all arms share)
    rng = random.Random(1)
    pool = [json.loads(l) for l in open("data/stage2_pool.jsonl")]
    s2 = [{"text": stage2_doc(ex)}
          for ex in rng.sample(pool, min(args.stage2_n, len(pool)))]
    if args.smoke:
        s2 = s2[:16]
    run(model, tok, tokenize(Dataset.from_list(s2), tok, args.seq),
        f"ckpt/{args.arm}_s2", 1, args.lr2, args.bs)
    assert_finite(model, "stage 2")

    outdir = f"ckpt/{args.arm}"
    model.save_pretrained(outdir)
    tok.save_pretrained(outdir)
    print(f"saved {outdir}")


if __name__ == "__main__":
    main()
