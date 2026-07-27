"""eval_cost.py: predict the witness from whatever the arm observes.
Primary metric: token accuracy over the 6 operation slots (chance 0.125).

Usage: python3 eval_cost.py --system q50 --arm sc_cost
"""
import argparse, json, os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from gen_cost import S, E, C, N, W, D, DI


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--n", type=int, default=300)
    a = ap.parse_args()
    ck = f"ckpt/{a.system}_{a.arm}"
    os.makedirs(f"results/{a.system}", exist_ok=True)
    tok = AutoTokenizer.from_pretrained(ck)
    model = AutoModelForCausalLM.from_pretrained(ck, dtype=torch.float32)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(dev).eval()
    eod = tok.convert_tokens_to_ids(D)

    items = []
    for i, line in enumerate(open(f"data/{a.system}/eval.jsonl")):
        if i >= a.n:
            break
        ex = json.loads(line)
        p = f"{S}\n{ex['start']}\n{E}\n{ex['end']}\n"
        if a.arm == "sc_cost":
            p += f"{C}\n{ex['cost']}\n"
        elif a.arm == "sc_costd":
            p += f"{C}\n{ex['cost']}\n{DI}\n{ex['dist']}\n"
        elif a.arm == "sc_counts":
            p += f"{N}\n{ex['counts']}\n"
        p += f"{W}\n"
        ids = tok(p, return_tensors="pt", truncation=True,
                  max_length=256).to(dev)
        with torch.no_grad():
            out = model.generate(**ids, max_new_tokens=32, do_sample=False,
                                 eos_token_id=eod,
                                 pad_token_id=tok.pad_token_id)
        gen = tok.decode(out[0][ids["input_ids"].shape[1]:],
                         skip_special_tokens=False)
        gen = gen.split(D)[0].split(S)[0].strip().split()
        gold = ex["witness"].split()
        hit = sum(1 for x, y in zip(gen, gold) if x == y)
        items.append(dict(i=i, tok_acc=round(hit / len(gold), 4),
                          exact=int(gen == gold)))
    n = len(items)
    summ = dict(system=a.system, arm=a.arm, n=n,
                tok_acc=round(sum(x["tok_acc"] for x in items) / n, 4),
                exact=round(sum(x["exact"] for x in items) / n, 4),
                items=items)
    json.dump(summ, open(f"results/{a.system}/{a.arm}.json", "w"), indent=1)
    print(f"{a.system} {a.arm}: tok_acc {summ['tok_acc']:.4f}  "
          f"exact {summ['exact']:.4f}")


if __name__ == "__main__":
    main()
