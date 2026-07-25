"""train_stage1.py: run ONLY stage 1 and save the checkpoint.

Part V varies the stage-2 budget while holding stage 1 fixed, so stage 1
is trained once per arm and reused. This script is stage 1 of the Part III
train.py, unchanged in protocol: same corpora, same fp32 load, same
learning rate, same finite-weights guard.

Usage: python3 train_stage1.py --arm pw_trace [--seed 0]
Writes: ckpt_s1/<arm>[_s<seed>]/
"""
import argparse, json, os

import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          DataCollatorForLanguageModeling, Trainer,
                          TrainingArguments)

B, T, A, E = "<|STATE_BEFORE|>", "<|TACTIC|>", "<|STATE_AFTER|>", "<|END|>"


def assert_finite(model, where):
    bad = [n for n, p in model.named_parameters()
           if not torch.isfinite(p).all()]
    if bad:
        raise RuntimeError(f"non-finite weights after {where}: {bad[:5]} "
                           f"({len(bad)} tensors). Lower --lr1.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["pw_trace", "pw_pair", "pw_endpoint",
                             "pw_shuffle"])
    ap.add_argument("--model", default="EleutherAI/pythia-160m")
    ap.add_argument("--epochs", type=float, default=1)
    ap.add_argument("--seq", type=int, default=768)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--lr1", type=float, default=5e-5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    tok = AutoTokenizer.from_pretrained(args.model)
    tok.add_special_tokens({"additional_special_tokens": [B, T, A, E]})
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model,
                                                 dtype=torch.float32)
    if len(tok) > model.get_input_embeddings().weight.shape[0]:
        model.resize_token_embeddings(len(tok), mean_resizing=False)

    rows = [json.loads(l) for l in open(f"data/{args.arm}_train.jsonl")]
    rows = [d for d in rows if len(d["text"].strip()) > 20]
    if args.smoke:
        rows = rows[:32]
    ds = Dataset.from_list(rows)
    ds = ds.map(lambda b: tok(b["text"], truncation=True,
                              max_length=args.seq),
                batched=True, remove_columns=ds.column_names)

    targs = TrainingArguments(
        output_dir=f"ckpt_s1/tmp_{args.arm}",
        num_train_epochs=1 if args.smoke else args.epochs,
        learning_rate=args.lr1, per_device_train_batch_size=args.bs,
        gradient_accumulation_steps=4, bf16=False, fp16=False,
        warmup_ratio=0.03, max_grad_norm=1.0, logging_steps=50,
        save_strategy="no", report_to=[])
    Trainer(model=model, args=targs, train_dataset=ds,
            data_collator=DataCollatorForLanguageModeling(tok, mlm=False)
            ).train()
    assert_finite(model, "stage 1")

    suf = "" if args.seed == 0 else f"_s{args.seed}"
    out = f"ckpt_s1/{args.arm}{suf}"
    model.save_pretrained(out)
    tok.save_pretrained(out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
