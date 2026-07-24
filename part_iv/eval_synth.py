"""eval_synth.py: predict the witness from the endpoint pair.

Primary metric is token accuracy over the L operation slots. Chance is
1/n_ops. The witness alphabet (OP0..OP7) is disjoint from the state
alphabet (binary digits), so copying the input cannot score above chance
and no echo correction is needed; the echo ceiling is reported anyway for
continuity with Parts I and III.

Records each item's EXACT fiber size, so accuracy can be regressed on
witness information at the item level as well as the condition level.

Usage: python3 eval_synth.py --opset q50 --arm sy_trace [--seed 0]
Writes: results/<opset>/eval_<arm>[_s<seed>].json
"""
import argparse, json, os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

S, W, E, END = "<|START|>", "<|WITNESS|>", "<|END_STATE|>", "<|EOD|>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--opset", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max_new", type=int, default=40)
    args = ap.parse_args()
    suf = "" if args.seed == 0 else f"_s{args.seed}"
    ck = f"ckpt/{args.opset}/{args.arm}{suf}"
    os.makedirs(f"results/{args.opset}", exist_ok=True)

    tok = AutoTokenizer.from_pretrained(ck)
    model = AutoModelForCausalLM.from_pretrained(ck, dtype=torch.float32)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(dev).eval()
    end_id = tok.convert_tokens_to_ids(END)

    items = []
    for i, line in enumerate(open(f"data/{args.opset}/eval.jsonl")):
        if i >= args.n:
            break
        ex = json.loads(line)
        gold = ex["witness"].split()
        prompt = f"{S}\n{ex['start']}\n{E}\n{ex['end']}\n{W}\n"
        ids = tok(prompt, return_tensors="pt", truncation=True,
                  max_length=512).to(dev)
        with torch.no_grad():
            out = model.generate(**ids, max_new_tokens=args.max_new,
                                 do_sample=False, eos_token_id=end_id,
                                 pad_token_id=tok.pad_token_id)
        gen = tok.decode(out[0][ids["input_ids"].shape[1]:],
                         skip_special_tokens=False)
        gen = gen.split(END)[0].split(S)[0].strip().split()
        hits = sum(1 for a, b in zip(gen, gold) if a == b)
        items.append(dict(i=i, fiber=ex["fiber"],
                          gen=" ".join(gen[:12]), gold=" ".join(gold),
                          exact=int(gen == gold),
                          tok_acc=round(hits / len(gold), 4),
                          n_pred=len(gen)))

    n = len(items)
    summary = dict(opset=args.opset, arm=args.arm, seed=args.seed, n=n,
                   exact_match=sum(x["exact"] for x in items) / n,
                   tok_acc_mean=sum(x["tok_acc"] for x in items) / n,
                   mean_fiber=sum(x["fiber"] for x in items) / n,
                   items=items)
    with open(f"results/{args.opset}/eval_{args.arm}{suf}.json", "w") as f:
        json.dump(summary, f, indent=1)
    for k in ("exact_match", "tok_acc_mean", "mean_fiber"):
        print(f"{k}: {summary[k]:.4f}")


if __name__ == "__main__":
    main()
