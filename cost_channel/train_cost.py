"""train_cost.py: one arm, one system. Single stage: the arm's corpus IS
the task format, so no separate adaptation is needed and all arms see
identical example counts.

Usage: python3 train_cost.py --system q50 --arm sc_cost
"""
import argparse, json, os

import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          DataCollatorForLanguageModeling, Trainer,
                          TrainingArguments)

from gen_cost import S, E, C, N, W, D, DI


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--arm", required=True,
                    choices=["sc_pair", "sc_cost", "sc_costd",
                             "sc_counts"])
    ap.add_argument("--model", default="EleutherAI/pythia-160m")
    ap.add_argument("--epochs", type=float, default=2)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--seq", type=int, default=128)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(a.seed)

    tok = AutoTokenizer.from_pretrained(a.model)
    tok.add_special_tokens({"additional_special_tokens":
                            [S, E, C, N, W, D, DI]})
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(a.model,
                                                 dtype=torch.float32)
    if len(tok) > model.get_input_embeddings().weight.shape[0]:
        model.resize_token_embeddings(len(tok), mean_resizing=False)

    rows = [json.loads(l) for l in
            open(f"data/{a.system}/{a.arm}_train.jsonl")]
    if a.smoke:
        rows = rows[:64]
    ds = Dataset.from_list(rows)
    ds = ds.map(lambda b: tok(b["text"], truncation=True,
                              max_length=a.seq),
                batched=True, remove_columns=ds.column_names)
    targs = TrainingArguments(
        output_dir=f"ckpt/tmp_{a.system}_{a.arm}",
        num_train_epochs=1 if a.smoke else a.epochs, learning_rate=a.lr,
        per_device_train_batch_size=a.bs, gradient_accumulation_steps=2,
        bf16=False, fp16=False, warmup_ratio=0.03, max_grad_norm=1.0,
        logging_steps=50, save_strategy="no", report_to=[])
    Trainer(model=model, args=targs, train_dataset=ds,
            data_collator=DataCollatorForLanguageModeling(tok, mlm=False)
            ).train()
    bad = [n for n, p in model.named_parameters()
           if not torch.isfinite(p).all()]
    if bad:
        raise RuntimeError(f"non-finite weights: {bad[:3]}")
    out = f"ckpt/{a.system}_{a.arm}"
    model.save_pretrained(out); tok.save_pretrained(out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
