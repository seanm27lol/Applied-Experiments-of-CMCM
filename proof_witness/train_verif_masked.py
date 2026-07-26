"""train_verif_masked.py: the registered V1 retry. Identical to
train_verif.py except the training loss is computed ONLY on the verdict
answer token (the ' yes'/' no' immediately after <|VERDICT|>); all other
positions are masked to -100. Same data, same order, same budgets.

Usage: python3 train_verif_masked.py --arm pw_trace --n 4000 [--seed 0]
Writes: ckpt/verifm_<arm>_n<N>[_s<seed>]/
"""
import argparse, os

import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                          TrainingArguments)

from train_verif import V, build_train


class MaskedCollator:
    def __init__(self, tok, vid):
        self.tok, self.vid = tok, vid

    def __call__(self, feats):
        batch = self.tok.pad(feats, return_tensors="pt")
        ids = batch["input_ids"]
        labels = torch.full_like(ids, -100)
        for r in range(ids.shape[0]):
            pos = (ids[r] == self.vid).nonzero(as_tuple=True)[0]
            for p in pos:
                if p + 1 < ids.shape[1]:
                    labels[r, p + 1] = ids[r, p + 1]
        batch["labels"] = labels
        return batch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--lr2", type=float, default=2e-5)
    ap.add_argument("--seq", type=int, default=640)
    ap.add_argument("--ckpt_s1_dir", default="ckpt_s1")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    suf = "" if args.seed == 0 else f"_s{args.seed}"
    ck = f"{args.ckpt_s1_dir}/{args.arm}{suf}"
    if not os.path.isdir(ck):
        raise SystemExit(f"missing stage-1 checkpoint {ck}")

    tok = AutoTokenizer.from_pretrained(ck)
    added = tok.add_special_tokens({"additional_special_tokens": [V]})
    model = AutoModelForCausalLM.from_pretrained(ck, dtype=torch.float32)
    if added:
        model.resize_token_embeddings(len(tok), mean_resizing=False)
    vid = tok.convert_tokens_to_ids(V)
    for lab in (" yes", " no"):
        assert len(tok(lab, add_special_tokens=False)["input_ids"]) == 1

    rows = build_train(args.n, args.seed)
    if args.smoke:
        rows = rows[:16]
    ds = Dataset.from_list(rows)
    ds = ds.map(lambda b: tok(b["text"], truncation=True,
                              max_length=args.seq),
                batched=True, remove_columns=ds.column_names)
    targs = TrainingArguments(
        output_dir=f"ckpt/tmp_vm_{args.arm}_{args.n}", num_train_epochs=1,
        learning_rate=args.lr2, per_device_train_batch_size=args.bs,
        gradient_accumulation_steps=4, bf16=False, fp16=False,
        warmup_ratio=0.03, max_grad_norm=1.0, logging_steps=25,
        save_strategy="no", report_to=[],
        remove_unused_columns=False)
    Trainer(model=model, args=targs, train_dataset=ds,
            data_collator=MaskedCollator(tok, vid)).train()
    bad = [p for _, p in model.named_parameters()
           if not torch.isfinite(p).all()]
    if bad:
        raise RuntimeError("non-finite weights after masked stage 2")
    out = f"ckpt/verifm_{args.arm}_n{args.n}{suf}"
    model.save_pretrained(out)
    tok.save_pretrained(out)
    print(f"saved {out}  ({len(rows)} instances, verdict-masked loss)")


if __name__ == "__main__":
    main()
