"""eval_verif.py: score verif_eval.jsonl by label-token logprob margin.

For each instance, teacher-force up to '<|VERDICT|>' and compare next-token
logprobs of ' yes' vs ' no'. margin > 0 predicts valid. No generation, so
no decoding confounds.

Usage: python3 eval_verif.py --arm pw_trace --n 4000 [--seed 0]
Writes: results/verif_<arm>_n<N>[_s<seed>].json
"""
import argparse, json, os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from train_verif import B, T, A, V, E, clip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--prefix", default="verif")
    args = ap.parse_args()
    suf = "" if args.seed == 0 else f"_s{args.seed}"
    tag = f"{args.prefix}_{args.arm}_n{args.n}{suf}"
    os.makedirs("results", exist_ok=True)

    tok = AutoTokenizer.from_pretrained(f"ckpt/{tag}")
    model = AutoModelForCausalLM.from_pretrained(f"ckpt/{tag}",
                                                 dtype=torch.float32)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(dev).eval()
    yid = tok(" yes", add_special_tokens=False)["input_ids"][0]
    nid = tok(" no", add_special_tokens=False)["input_ids"][0]

    items = []
    for line in open("verif_eval.jsonl"):
        ex = json.loads(line)
        prompt = (f"{B}\n{clip(ex['state'])}\n{T}\n{ex['tactic']}\n"
                  f"{A}\n{clip(ex['target_state'])}\n{V}")
        ids = tok(prompt, return_tensors="pt", truncation=True,
                  max_length=1024).to(dev)
        with torch.no_grad():
            lp = model(**ids).logits[0, -1].log_softmax(-1)
        m = (lp[yid] - lp[nid]).item()
        items.append(dict(idx=ex["idx"], stratum=ex["stratum"],
                          label=ex["label_valid"], margin=round(m, 4),
                          correct=int((m > 0) == bool(ex["label_valid"]))))
    n = len(items)
    acc = sum(x["correct"] for x in items) / n
    summ = dict(arm=args.arm, n_budget=args.n, seed=args.seed,
                n_items=n, accuracy=round(acc, 4), items=items)
    with open(f"results/{tag}.json", "w") as f:
        json.dump(summ, f, indent=1)
    from collections import defaultdict
    per = defaultdict(list)
    for x in items:
        per[x["stratum"]].append(x["correct"])
    print(f"overall accuracy {acc:.4f}")
    for s in sorted(per):
        print(f"  {s:<6} n={len(per[s]):>3}  "
              f"acc={sum(per[s])/len(per[s]):.4f}")


if __name__ == "__main__":
    main()
