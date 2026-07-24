"""train_synth.py: two-stage training for one arm of one fiber condition.

Stage 1 differs by arm (the arm's corpus). Stage 2 is identical for every
arm: predict the witness from the endpoint pair. Same protocol as Parts I
and III, including the fp32 load that Part III's divergence made necessary.

Usage: python3 train_synth.py --opset q50 --arm sy_trace [--seed 0]
Writes: ckpt/<opset>/<arm>[_s<seed>]/
"""
import argparse, json, os, random

import torch
from datasets import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          DataCollatorForLanguageModeling, Trainer,
                          TrainingArguments)

S, W, E, END = "<|START|>", "<|WITNESS|>", "<|END_STATE|>", "<|EOD|>"


def stage2_doc(ex):
    return (f"{S}\n{ex['start']}\n{E}\n{ex['end']}\n"
            f"{W}\n{ex['witness']}\n{END}\n")


def assert_finite(model, where):
    bad = [n for n, p in model.named_parameters()
           if not torch.isfinite(p).all()]
    if bad:
        raise RuntimeError(f"non-finite weights after {where}: {bad[:5]} "
                           f"({len(bad)} tensors). Lower --lr1/--lr2.")


def run(model, tok, ds, outdir, epochs, lr, bs, seq):
    args = TrainingArguments(
        output_dir=outdir, num_train_epochs=epochs, learning_rate=lr,
        per_device_train_batch_size=bs, gradient_accumulation_steps=4,
        bf16=False, fp16=False, warmup_ratio=0.03, max_grad_norm=1.0,
        logging_steps=50, save_strategy="no", report_to=[])
    Trainer(model=model, args=args, train_dataset=ds,
            data_collator=DataCollatorForLanguageModeling(tok, mlm=False)
            ).train()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--opset", required=True)
    ap.add_argument("--arm", required=True,
                    choices=["sy_trace", "sy_pair", "sy_endpoint",
                             "sy_shuffle"])
    ap.add_argument("--model", default="EleutherAI/pythia-160m")
    ap.add_argument("--stage2_n", type=int, default=2000)
    ap.add_argument("--epochs", type=float, default=1)
    ap.add_argument("--seq", type=int, default=256)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr1", type=float, default=5e-5)
    ap.add_argument("--lr2", type=float, default=2e-5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    d = os.path.join("data", args.opset)
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.add_special_tokens({"additional_special_tokens": [S, W, E, END]})
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    # pythia configs declare float16; transformers>=5 honours that and
    # AdamW on raw fp16 weights overflows immediately. Force fp32.
    model = AutoModelForCausalLM.from_pretrained(args.model,
                                                 dtype=torch.float32)
    if len(tok) > model.get_input_embeddings().weight.shape[0]:
        model.resize_token_embeddings(len(tok), mean_resizing=False)

    def tk(rows):
        ds = Dataset.from_list(rows)
        return ds.map(lambda b: tok(b["text"], truncation=True,
                                    max_length=args.seq),
                      batched=True, remove_columns=ds.column_names)

    s1 = [json.loads(l) for l in open(f"{d}/{args.arm}_train.jsonl")]
    s1 = [x for x in s1 if len(x["text"].strip()) > 20]
    if args.smoke:
        s1 = s1[:32]
    run(model, tok, tk(s1), f"ckpt/{args.opset}/{args.arm}_s1",
        1 if args.smoke else args.epochs, args.lr1, args.bs, args.seq)
    assert_finite(model, "stage 1")

    rng = random.Random(1 + args.seed)
    pool = [json.loads(l) for l in open(f"{d}/eval.jsonl")]
    # stage 2 draws from TRAIN witnesses, never the held-out eval rows
    tr = [json.loads(l) for l in open(f"{d}/sy_trace_train.jsonl")]
    parsed = []
    for x in tr:
        t = x["text"]
        try:
            a = t.split(S)[1].split(W)[0].strip()
            w = t.split(W)[1].split(E)[0].strip()
            b = t.split(E)[1].split(END)[0].strip()
            parsed.append(dict(start=a, witness=w, end=b))
        except IndexError:
            continue
    s2 = [{"text": stage2_doc(x)}
          for x in rng.sample(parsed, min(args.stage2_n, len(parsed)))]
    if args.smoke:
        s2 = s2[:16]
    run(model, tok, tk(s2), f"ckpt/{args.opset}/{args.arm}_s2",
        1, args.lr2, args.bs, args.seq)
    assert_finite(model, "stage 2")

    suf = "" if args.seed == 0 else f"_s{args.seed}"
    out = f"ckpt/{args.opset}/{args.arm}{suf}"
    model.save_pretrained(out)
    tok.save_pretrained(out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
