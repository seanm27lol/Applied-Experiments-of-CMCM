"""search_cost.py: Sebastien Seboih's search procedure, measured.

Take a trained cost-conditioned model, fix (start, end), and ask it for
progressively CHEAPER paths. Then verify each generation by running it
forward: does it reach the recorded end state, and does it cost what was
requested? Generation is unreliable; verification is cheap. That is the
asymmetry the whole project is about, used as a search loop.

Only costs that are ACHIEVABLE for that endpoint pair are requested, so
a failure means the model failed rather than that the request was
impossible. One deliberately impossible request per item serves as the
control: a model that "succeeds" there is ignoring the cost field.

Usage: python3 search_cost.py --system q50 --arm sc_cost
Writes: results/<system>/search_<arm>.json
"""
import argparse, json, os
from collections import defaultdict
from itertools import product

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import ops as O
from gen_cost import S, E, C, N, W, D, DI, cost_of, counts_of, dist_of

L = 6


def achievable_costs(fns):
    """end state -> sorted list of distinct achievable costs, and the
    cheapest witness for each (end, cost) pair."""
    by_end = defaultdict(set)
    for seq in product(range(8), repeat=L):
        s = O.START
        for k in seq:
            s = fns[k](s)
        by_end[s].add(cost_of(seq))
    return {e: sorted(v) for e, v in by_end.items()}


def run_path(fns, seq):
    s = O.START
    for k in seq:
        s = fns[k](s)
    return s


def parse(gen):
    out = []
    for t in gen:
        if not t.startswith("OP") or not t[2:].isdigit():
            return None
        v = int(t[2:])
        if not 0 <= v < 8:
            return None
        out.append(v)
    return out if len(out) == L else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--arm", default="sc_cost",
                    choices=["sc_cost", "sc_costd"])
    ap.add_argument("--n", type=int, default=150)
    a = ap.parse_args()

    fns = [f for f, _ in O.build(a.system)]
    ck = f"ckpt/{a.system}_{a.arm}"
    tok = AutoTokenizer.from_pretrained(ck)
    model = AutoModelForCausalLM.from_pretrained(ck, dtype=torch.float32)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(dev).eval()
    eod = tok.convert_tokens_to_ids(D)
    costs = achievable_costs(fns)

    rows, rung_stats, skipped = [], defaultdict(lambda: [0, 0, 0]), 0
    for i, line in enumerate(open(f"data/{a.system}/eval.jsonl")):
        if i >= a.n:
            break
        ex = json.loads(line)
        end = int(ex["end"], 16)
        avail = costs.get(end, [])
        if len(avail) < 2:
            skipped += 1
            continue  # only one achievable cost: nothing to search over
        ladder = [("true", ex["cost"]),
                  ("median", avail[len(avail) // 2]),
                  ("min", avail[0]),
                  ("impossible", avail[0] - 2)]
        for rung, c in ladder:
            p = f"{S}\n{ex['start']}\n{E}\n{ex['end']}\n{C}\n{c}\n"
            if a.arm == "sc_costd":
                p += f"{DI}\n{ex['dist']}\n"
            p += f"{W}\n"
            ids = tok(p, return_tensors="pt", truncation=True,
                      max_length=256).to(dev)
            with torch.no_grad():
                out = model.generate(**ids, max_new_tokens=32,
                                     do_sample=False, eos_token_id=eod,
                                     pad_token_id=tok.pad_token_id)
            gen = tok.decode(out[0][ids["input_ids"].shape[1]:],
                             skip_special_tokens=False)
            seq = parse(gen.split(D)[0].split(S)[0].strip().split())
            reaches = seq is not None and run_path(fns, seq) == end
            matches = seq is not None and cost_of(seq) == c
            st = rung_stats[rung]
            st[0] += 1; st[1] += int(reaches); st[2] += int(reaches and matches)
            rows.append(dict(i=i, rung=rung, asked=c,
                             parsed=seq is not None, reaches=int(reaches),
                             cost_match=int(matches),
                             cheaper=int(reaches and matches
                                         and c < ex["cost"])))

    summ = dict(system=a.system, arm=a.arm, skipped_single_cost=skipped,
                n_items=len(set(r["i"] for r in rows)),
                rungs={k: dict(n=v[0], reaches=round(v[1]/v[0], 4),
                               valid_and_cost=round(v[2]/v[0], 4))
                       for k, v in rung_stats.items()},
                items=rows)
    os.makedirs(f"results/{a.system}", exist_ok=True)
    json.dump(summ, open(f"results/{a.system}/search_{a.arm}.json", "w"),
              indent=1)
    print(f"{a.system} {a.arm}  ({summ['n_items']} searchable items, "
          f"{skipped} skipped for having one achievable cost)")
    for k in ("true", "median", "min", "impossible"):
        if k in summ["rungs"]:
            r = summ["rungs"][k]
            print(f"  {k:<11} n={r['n']:>4}  reaches end {r['reaches']:.3f}"
                  f"   valid+cost {r['valid_and_cost']:.3f}")


if __name__ == "__main__":
    main()
