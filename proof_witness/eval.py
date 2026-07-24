"""eval.py: predict the tactic given (STATE_BEFORE, STATE_AFTER); score with
copy-robust metrics per the Part I lesson.

Metrics per item:
  exact       - normalized string equality with the gold tactic
  sim         - normalized Levenshtein similarity to gold
  echo_ceiling- best similarity achievable by copying any same-length
                substring of the input states (a pure copier scores ~this)
  sim_minus_echo - the headline metric; copying scores ~0
  recoverable - gold tactic appears verbatim in the input states (diagnostic)

Usage: python3 eval.py --arm pw_trace [--n 300] [--max_new 64]
Writes: results/eval_<arm>.json  (summary + per-item list, Part I style)
"""
import argparse, re, json, os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

B, T, A, E = "<|STATE_BEFORE|>", "<|TACTIC|>", "<|STATE_AFTER|>", "<|END|>"
MAX_STATE = 1200


def detag(s):
    return re.sub(r"</?a>", "", s or "")


def clip(s):
    s = (s or "").strip()
    return s[-MAX_STATE:] if len(s) > MAX_STATE else s


def lev(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def sim(a, b):
    a, b = a.strip(), b.strip()
    if not a and not b:
        return 1.0
    m = max(len(a), len(b))
    return 1 - lev(a, b) / m if m else 1.0


def echo_ceiling(gold, source, stride=7):
    g = gold.strip()
    if not g:
        return 0.0
    best, L = 0.0, len(g)
    for i in range(0, max(1, len(source) - L), stride):
        best = max(best, sim(g, source[i:i + L]))
        if best > 0.999:
            break
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--max_new", type=int, default=64)
    args = ap.parse_args()
    os.makedirs("results", exist_ok=True)

    tok = AutoTokenizer.from_pretrained(f"ckpt/{args.arm}")
    model = AutoModelForCausalLM.from_pretrained(f"ckpt/{args.arm}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    end_id = tok.convert_tokens_to_ids(E)

    items = []
    for i, line in enumerate(open("data/eval.jsonl")):
        if i >= args.n:
            break
        ex = json.loads(line)
        b, a, gold = clip(ex["state"]), clip(ex["target_state"]), detag(ex["tactic"]).strip()
        prompt = f"{B}\n{b}\n{A}\n{a}\n{T}\n"
        ids = tok(prompt, return_tensors="pt", truncation=True,
                  max_length=1024).to(device)
        with torch.no_grad():
            out = model.generate(**ids, max_new_tokens=args.max_new,
                                 do_sample=False, eos_token_id=end_id,
                                 pad_token_id=tok.pad_token_id)
        gen = tok.decode(out[0][ids["input_ids"].shape[1]:],
                         skip_special_tokens=False)
        gen = gen.split(E)[0].split(A)[0].strip()
        src = b + "\n" + a
        s = sim(gen, gold)
        ec = echo_ceiling(gold, src)
        items.append(dict(i=i, gen=gen[:200], gold=gold,
                          exact=int(gen == gold), sim=round(s, 4),
                          echo_ceiling=round(ec, 4),
                          sim_minus_echo=round(s - ec, 4),
                          recoverable=int(gold in src)))

    n = len(items)
    summary = dict(
        arm=args.arm, n=n,
        exact_match=sum(x["exact"] for x in items) / n,
        sim_mean=sum(x["sim"] for x in items) / n,
        sim_minus_echo_mean=sum(x["sim_minus_echo"] for x in items) / n,
        recoverable_rate=sum(x["recoverable"] for x in items) / n,
        items=items)
    with open(f"results/eval_{args.arm}.json", "w") as f:
        json.dump(summary, f, indent=1)
    for k in ("exact_match", "sim_mean", "sim_minus_echo_mean",
              "recoverable_rate"):
        print(f"{k}: {summary[k]:.4f}")


if __name__ == "__main__":
    main()
