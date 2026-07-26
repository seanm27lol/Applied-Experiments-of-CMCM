"""train_verif.py: verification stage 2 on a saved stage-1 checkpoint.

Docs: <|STATE_BEFORE|> s <|TACTIC|> t <|STATE_AFTER|> a <|VERDICT|> yes/no <|END|>
Negatives for TRAINING are generated from stage2_pool with the same
goal-closing filter and stratum mix as the eval builder, from TRAIN
theorems only. For a given (N, seed) every arm sees identical examples
in identical order (draw depends only on N, seed).

Usage: python3 train_verif.py --arm pw_trace --n 4000 [--seed 0]
Writes: ckpt/verif_<arm>_n<N>[_s<seed>]/
"""
import argparse, json, os, random, re

import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          DataCollatorForLanguageModeling, Trainer,
                          TrainingArguments)

import build_verif_eval as G

B, T, A, V, E = ("<|STATE_BEFORE|>", "<|TACTIC|>", "<|STATE_AFTER|>",
                 "<|VERDICT|>", "<|END|>")
MAX_STATE = 900


def clip(s):
    s = (s or "").strip()
    return s[-MAX_STATE:] if len(s) > MAX_STATE else s


def doc(state, tactic, after, valid):
    return (f"{B}\n{clip(state)}\n{T}\n{tactic}\n{A}\n{clip(after)}\n"
            f"{V} {'yes' if valid else 'no'}\n{E}\n")


def build_train(n, seed):
    rng = random.Random(100 + seed)
    pool = [json.loads(l) for l in open("data/stage2_pool.jsonl" if __import__("os").path.exists("data/stage2_pool.jsonl") else "stage2_pool.jsonl")]
    order = list(range(len(pool)))
    rng.shuffle(order)
    tacs = [(pool[i]["full_name"], pool[i]["tactic"].strip(),
             pool[i]["state"]) for i in order]
    rows, i = [], 0
    while len(rows) < n and i < len(order):
        r = pool[order[i]]; i += 1
        gold, st, aft = r["tactic"].strip(), r["state"], r["target_state"]
        rows.append({"text": doc(st, gold, aft, True)})
        if len(rows) >= n: break
        if G.closing(aft):  # after-swap negative
            alt = pool[order[(i * 7 + 3) % len(order)]]["target_state"]
            if alt != aft:
                rows.append({"text": doc(st, gold, alt, False)})
        else:               # tactic-swap negative, screened
            for k in range(40):
                th, t2, _ = tacs[(i * 13 + k) % len(tacs)]
                if th != r["full_name"] and t2 != gold:
                    rows.append({"text": doc(st, t2, aft, False)})
                    break
    rng.shuffle(rows)
    return rows[:n]


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
    for lab in (" yes", " no"):
        assert len(tok(lab, add_special_tokens=False)["input_ids"]) == 1, \
            f"label {lab!r} is not a single token"

    rows = build_train(args.n, args.seed)
    if args.smoke:
        rows = rows[:16]
    ds = Dataset.from_list(rows)
    ds = ds.map(lambda b: tok(b["text"], truncation=True,
                              max_length=args.seq),
                batched=True, remove_columns=ds.column_names)
    targs = TrainingArguments(
        output_dir=f"ckpt/tmp_v_{args.arm}_{args.n}", num_train_epochs=1,
        learning_rate=args.lr2, per_device_train_batch_size=args.bs,
        gradient_accumulation_steps=4, bf16=False, fp16=False,
        warmup_ratio=0.03, max_grad_norm=1.0, logging_steps=25,
        save_strategy="no", report_to=[])
    Trainer(model=model, args=targs, train_dataset=ds,
            data_collator=DataCollatorForLanguageModeling(tok, mlm=False)
            ).train()
    bad = [p for _, p in model.named_parameters()
           if not torch.isfinite(p).all()]
    if bad:
        raise RuntimeError("non-finite weights after verification stage 2")
    out = f"ckpt/verif_{args.arm}_n{args.n}{suf}"
    model.save_pretrained(out); tok.save_pretrained(out)
    print(f"saved {out}  ({len(rows)} training instances)")


if __name__ == "__main__":
    main()
