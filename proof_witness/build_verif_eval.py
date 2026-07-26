"""build_verif_eval.py: the verification eval set, stratified negatives,
automated screens, and pre-annotated audit sheets.

Goal-closing rule: steps whose true after-state is 'no goals' are EXCLUDED
as tactic-swap TARGETS (S1-S4), because any other closing tactic that
happens to work reproduces the same after-state and silently mislabels.
They are retained as S5 targets and as swap SOURCES (a swapped closing
tactic on a non-closing target yields 'no goals' != recorded after, so
the invalid label is certain).

Stratum assignment: non-closing stems round-robin S1-S4; closing stems
to S5. Negative tactic sources: train pool (S1/S2), same-theorem eval
siblings (S3), in-context corruption (S4).

Machine confidence tiers for the two-tier audit:
  CONF: S1 (low overlap), S5 (after mismatch is string-checkable)
  UNC:  S2, S3, S4 (semantic judgment needed)
"""
import json, random, re
from collections import defaultdict


def toks(s): return set(re.findall(r"[A-Za-z_][A-Za-z0-9_.']*", s))
def overlap(t, st):
    tt = toks(t); return len(tt & toks(st)) / max(len(tt), 1)
def closing(after): return 'no goals' in after.lower() or not after.strip()
def hyps(state):
    out = []
    for line in state.splitlines():
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_']*)\s*[:✝]", line.strip())
        if m and not m.group(1).startswith("inst"):
            out.append(m.group(1))
    return out
def tail(s, n=2): return " | ".join(s.strip().splitlines()[-n:])[:160]


def main():
    rng = random.Random(0)
    ev = [json.loads(l) for l in open("eval.jsonl")]
    pool = [json.loads(l) for l in open("stage2_pool.jsonl")]
    by_thm = defaultdict(list)
    for r in ev: by_thm[r["full_name"]].append(r)
    # dup screen index over what we can see
    seen = {}
    for r in pool + ev:
        seen[(r["state"], r["tactic"].strip())] = r["target_state"]

    pool_tacs = [(r["full_name"], r["tactic"].strip(), r["state"])
                 for r in pool]
    non_close = [r for r in ev if not closing(r["target_state"])]
    close = [r for r in ev if closing(r["target_state"])]
    print(f"stems: {len(non_close)} non-closing -> S1-S4; "
          f"{len(close)} closing -> S5")

    out, sheets = [], defaultdict(list)

    def screen(item, neg_tac):
        if neg_tac is None: return False
        if neg_tac.strip() == item["tactic"].strip(): return False
        prev = seen.get((item["state"], neg_tac.strip()))
        if prev is not None and prev == item["target_state"]: return False
        return True

    for i, r in enumerate(non_close):
        S = ["S1", "S2", "S3", "S4"][i % 4]
        gold, st = r["tactic"].strip(), r["state"]
        neg = None
        if S == "S1":
            c = [t for th, t, _ in pool_tacs
                 if th != r["full_name"] and overlap(t, st) < 0.2]
            rng.shuffle(c)
            neg = next((t for t in c if screen(r, t)), None)
        elif S == "S2":
            c = [t for th, t, _ in pool_tacs
                 if th != r["full_name"] and overlap(t, st) >= 0.5]
            rng.shuffle(c)
            neg = next((t for t in c if screen(r, t)), None)
        elif S == "S3":
            sib = [x["tactic"].strip() for x in by_thm[r["full_name"]]
                   if x["tactic"].strip() != gold]
            rng.shuffle(sib)
            neg = next((t for t in sib if screen(r, t)), None)
            if neg is None: S = "S2"; continue_s2 = True
        if S == "S4" or (S != "S4" and neg is None and S in ("S1","S2")):
            pass
        if S == "S4":
            used = [h for h in hyps(st) if re.search(rf"\b{re.escape(h)}\b", gold)]
            others = [h for h in hyps(st) if h not in used]
            rng.shuffle(used); rng.shuffle(others)
            for a in used:
                for b in others:
                    cand = re.sub(rf"\b{re.escape(a)}\b", b, gold, count=1)
                    if screen(r, cand): neg = cand; break
                if neg: break
        if neg is None:  # fallback: S2-style
            c = [t for th, t, _ in pool_tacs if th != r["full_name"]]
            rng.shuffle(c)
            neg = next((t for t in c if screen(r, t)), None)
            S = S + "f"
        conf = "CONF" if S.startswith("S1") else "UNC"
        out.append(dict(idx=len(out), stratum=S, label_valid=0, conf=conf,
                        state=r["state"], tactic=neg,
                        target_state=r["target_state"], gold=gold))
        sheets[S[:2]].append((len(out)-1, conf, tail(st), gold[:120],
                              neg[:120], tail(r["target_state"])))
        out.append(dict(idx=len(out), stratum="VALID", label_valid=1,
                        conf="CONF", state=r["state"], tactic=gold,
                        target_state=r["target_state"], gold=gold))

    for r in close:
        alts = [x["target_state"] for x in ev
                if x["target_state"] != r["target_state"]
                and not closing(x["target_state"])]
        neg_after = rng.choice(alts)
        out.append(dict(idx=len(out), stratum="S5", label_valid=0,
                        conf="CONF", state=r["state"],
                        tactic=r["tactic"].strip(),
                        target_state=neg_after, gold=r["tactic"].strip()))
        sheets["S5"].append((len(out)-1, "CONF", tail(r["state"]),
                             r["tactic"].strip()[:120],
                             "AFTER swapped to: " + tail(neg_after),
                             tail(r["target_state"])))
        out.append(dict(idx=len(out), stratum="VALID", label_valid=1,
                        conf="CONF", state=r["state"],
                        tactic=r["tactic"].strip(),
                        target_state=r["target_state"],
                        gold=r["tactic"].strip()))

    with open("verif_eval.jsonl", "w") as f:
        for o in out: f.write(json.dumps(o) + "\n")
    from collections import Counter
    print(Counter(o["stratum"] for o in out))

    rng2 = random.Random(7)
    for S, rows in sheets.items():
        k = 15 if S in ("S2", "S3", "S4") else 8
        take = rng2.sample(rows, min(k, len(rows)))
        with open(f"audit_{S}.md", "w") as f:
            f.write(f"# V0 audit sheet {S} ({len(take)} items)\n")
            f.write("Mark [x] ONLY if the negative could be VALID "
                    "(tactic reproduces the recorded after-state).\n\n")
            for idx, conf, st, gold, neg, aft in take:
                f.write(f"### item {idx}  [{conf}]\n- [ ] MISLABELED?\n"
                        f"GOAL: {st}\nTRUE AFTER: {aft}\nGOLD: {gold}\n"
                        f"NEG : {neg}\n\n")
        print(f"audit_{S}.md: {len(take)} items")


if __name__ == "__main__":
    main()
