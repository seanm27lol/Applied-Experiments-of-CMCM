"""mine_mathlib_diffs.py: extract edit-witness triples from mathlib4 history.

For every non-merge commit that modifies exactly one Mathlib/**/*.lean file
with a modest diff, emit up to 3 hunk records:
    {sha, date, path, before, after, diff}
where `before`/`after` are windowed slices of the file around the hunk and
`diff` is the unified diff of those windows: the transformation witness.

Usage:
    python mine_mathlib_diffs.py --repo ml4 --out edits.jsonl [--max-commits N]

Filters: single-file .lean modification (no adds/deletes/renames), total
changed lines <= 60, path under Mathlib/, skips deprecation sweeps and
dependency bumps, dedupes by (before, diff) hash. Output is sorted by
commit date ascending so a time-based train/test split is a simple tail cut.
"""

import argparse, difflib, hashlib, json, subprocess, sys

CTX_BEFORE = 25   # context lines above the hunk
CTX_AFTER = 10    # context lines below the hunk
MAX_CHANGED = 60  # max total changed lines per commit
MAX_HUNKS = 3     # max records per commit
SKIP_SUBJECT = ("chore(deps", "bump ", "update dependencies")
SKIP_PATH = ("Deprecated",)


def git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True).stdout


def blob(repo, rev, path):
    r = subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def hunks(a_lines, b_lines):
    sm = difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    for group in sm.get_grouped_opcodes(n=0):
        i1 = min(op[1] for op in group)
        i2 = max(op[2] for op in group)
        j1 = min(op[3] for op in group)
        j2 = max(op[4] for op in group)
        yield i1, i2, j1, j2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-commits", type=int, default=None)
    args = ap.parse_args()

    log = git(args.repo, "log", "--no-merges",
              "--pretty=%H\x1f%ad\x1f%s", "--date=short").splitlines()
    if args.max_commits:
        log = log[: args.max_commits]

    seen, records = set(), []
    n_commits = n_singlefile = 0
    for line in log:
        try:
            sha, date, subject = line.split("\x1f", 2)
        except ValueError:
            continue
        n_commits += 1
        subj = subject.lower()
        if any(subj.startswith(s) for s in SKIP_SUBJECT):
            continue
        stat = git(args.repo, "diff-tree", "--no-commit-id",
                   "--numstat", "-r", sha).splitlines()
        if len(stat) != 1:
            continue
        parts = stat[0].split("\t")
        if len(parts) != 3:
            continue
        added, removed, path = parts
        if not (path.startswith("Mathlib/") and path.endswith(".lean")):
            continue
        if any(s in path for s in SKIP_PATH):
            continue
        if added == "-" or removed == "-":  # binary
            continue
        if int(added) + int(removed) > MAX_CHANGED:
            continue
        before_txt = blob(args.repo, f"{sha}^", path)
        after_txt = blob(args.repo, sha, path)
        if before_txt is None or after_txt is None:  # add/delete, shallow edge
            continue
        n_singlefile += 1
        a, b = before_txt.splitlines(), after_txt.splitlines()
        for k, (i1, i2, j1, j2) in enumerate(hunks(a, b)):
            if k >= MAX_HUNKS:
                break
            lo = max(0, i1 - CTX_BEFORE)
            hi = min(len(a), i2 + CTX_AFTER)
            # map the same context window into the after file
            blo = max(0, j1 - (i1 - lo))
            bhi = min(len(b), j2 + (hi - i2))
            bw = "\n".join(a[lo:hi])
            aw = "\n".join(b[blo:bhi])
            dw = "\n".join(difflib.unified_diff(
                a[lo:hi], b[blo:bhi], lineterm="", n=3))
            if not dw.strip():
                continue
            h = hashlib.sha1((bw + "\x00" + dw).encode()).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            records.append(dict(sha=sha, date=date, path=path,
                                before=bw, after=aw, diff=dw))

    records.sort(key=lambda r: r["date"])
    with open(args.out, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"commits scanned {n_commits} | single-file .lean {n_singlefile} "
          f"| records {len(records)} -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
