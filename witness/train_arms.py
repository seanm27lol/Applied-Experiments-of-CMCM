"""train_arms.py: matched-compute training arms for the edit-witness experiment.

Arms (identical pipeline, only the formatting differs):
  diff      : "### BEFORE\\n{before}\\n### DIFF\\n{diff}\\n<END>"   (the witness)
  after     : "### BEFORE\\n{before}\\n### AFTER\\n{after}\\n<END>" (endpoint map)
  endpoint  : "{after}\\n<END>"                                     (endpoint-only LM)

Fairness contract: every arm consumes exactly --target-tokens tokens from the
same date-sorted training split (last --test-frac of records is NEVER seen),
same base model, same LoRA config, same optimizer and schedule, same seed.

Stage 2 (shared adaptation for the transfer test): pass --init <prior ckpt>
and train the SAME small budget on --arm diff from each Stage-1 checkpoint.

Usage (smoke):
  python train_arms.py --data edits.jsonl --arm diff --model EleutherAI/pythia-14m \
      --target-tokens 8000 --seq-len 256 --out ck_smoke_diff
Usage (real):
  python train_arms.py --data edits.jsonl --arm diff --model EleutherAI/pythia-410m \
      --target-tokens 20000000 --out ck_diff --seed 0
"""

import argparse, csv, json, math, os, random, time

import torch
from torch.optim import AdamW
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, PeftModel

FORMATS = {
    "diff": "### BEFORE\n{before}\n### DIFF\n{diff}\n<END>",
    "after": "### BEFORE\n{before}\n### AFTER\n{after}\n<END>",
    "endpoint": "{after}\n<END>",
}


def load_split(path, test_frac):
    recs = [json.loads(l) for l in open(path)]
    cut = int(len(recs) * (1 - test_frac))
    return recs[:cut], recs[cut:]  # miner output is date-sorted


def token_stream(recs, tok, arm, seq_len, target_tokens, seed):
    rng = random.Random(seed)
    order = list(range(len(recs)))
    buf, served = [], 0
    while served < target_tokens:
        rng.shuffle(order)
        for i in order:
            text = FORMATS[arm].format(**recs[i])
            buf.extend(tok(text, add_special_tokens=False)["input_ids"])
            buf.append(tok.eos_token_id)
            while len(buf) >= seq_len and served < target_tokens:
                yield torch.tensor(buf[:seq_len], dtype=torch.long)
                buf = buf[seq_len:]
                served += seq_len
            if served >= target_tokens:
                return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--arm", choices=list(FORMATS), required=True)
    ap.add_argument("--model", default="EleutherAI/pythia-410m")
    ap.add_argument("--out", required=True)
    ap.add_argument("--target-tokens", type=int, default=20_000_000)
    ap.add_argument("--seq-len", type=int, default=1024)
    ap.add_argument("--batch-tokens", type=int, default=8192)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--test-frac", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--init", default=None, help="prior LoRA ckpt (Stage 2)")
    ap.add_argument("--log-every", type=int, default=20)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = (torch.bfloat16 if device == "cuda"
             and torch.cuda.is_bf16_supported() else torch.float32)

    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.eos_token_id is None:
        tok.add_special_tokens({"eos_token": "<|endoftext|>"})
    base = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=dtype)
    if args.init:
        model = PeftModel.from_pretrained(base, args.init, is_trainable=True)
    else:
        lcfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                          target_modules=["query_key_value"],
                          task_type="CAUSAL_LM")
        model = get_peft_model(base, lcfg)
    model.to(device)
    model.train()

    train, _ = load_split(args.data, args.test_frac)
    micro_bs = max(1, args.batch_tokens // args.seq_len)
    stream = token_stream(train, tok, args.arm, args.seq_len,
                          args.target_tokens, args.seed)
    opt = AdamW((p for p in model.parameters() if p.requires_grad), lr=args.lr)

    os.makedirs(args.out, exist_ok=True)
    log = csv.writer(open(os.path.join(args.out, "loss_curve.csv"), "w"))
    log.writerow(["step", "tokens", "loss"])
    json.dump(vars(args), open(os.path.join(args.out, "config.json"), "w"),
              indent=1)

    step, tokens_seen, ema, t0 = 0, 0, None, time.time()
    done = False
    while not done:
        batch = []
        for _ in range(micro_bs):
            x = next(stream, None)
            if x is None:
                done = True
                break
            batch.append(x)
        if not batch:
            break
        ids = torch.stack(batch).to(device)
        out = model(input_ids=ids, labels=ids)
        out.loss.backward()
        torch.nn.utils.clip_grad_norm_(
            (p for p in model.parameters() if p.requires_grad), 1.0)
        opt.step()
        opt.zero_grad(set_to_none=True)
        step += 1
        tokens_seen += ids.numel()
        l = out.loss.item()
        ema = l if ema is None else 0.98 * ema + 0.02 * l
        if step % args.log_every == 0:
            rate = tokens_seen / (time.time() - t0)
            print(f"step {step} | tokens {tokens_seen} | loss {l:.4f} "
                  f"| ema {ema:.4f} | {rate:.0f} tok/s", flush=True)
            log.writerow([step, tokens_seen, round(l, 5)])
    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    print(f"done: {tokens_seen} tokens, final ema loss {ema:.4f} -> {args.out}")


if __name__ == "__main__":
    main()
