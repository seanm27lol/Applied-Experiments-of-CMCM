"""fig7_decomposition.py: regenerate Figure 7 (content/format decomposition).

Recomputes the trace-vs-pair gap decomposition on sim_minus_echo from the
committed per-item eval JSONs and plots stacked bars at the two operating
points:

  Part III (N = 2000): eval_pw_trace.json / eval_pw_shuffle.json / eval_pw_pair.json
      content (trace - shuffle) +0.0393, format (shuffle - pair) +0.0146
      -> content share 73%   (PREREGISTRATION.md verdicts, 2026-07-24)
  Part V  (N = 4000):  eval_pw_{trace,shuffle,pair}_n4000.json
      content +0.0563, format +0.0266 -> content share 68%
      (conditional secondary registered in ../part_v/PREREGISTRATION.md)

Outputs: ~/Downloads/figure7_decomposition.png and .pdf
Run: ../.venv/bin/python fig7_decomposition.py
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT_DIR = Path.home() / "Downloads"

ARMS = {
    "Part III\n(N = 2000)": ("eval_pw_trace.json", "eval_pw_shuffle.json", "eval_pw_pair.json"),
    "Part V\n(N = 4000)": ("eval_pw_trace_n4000.json", "eval_pw_shuffle_n4000.json", "eval_pw_pair_n4000.json"),
}


def items(fname):
    return json.load(open(RESULTS / fname))["items"]


def mean_delta(a, b):
    d = [x["sim_minus_echo"] - y["sim_minus_echo"] for x, y in zip(a, b)]
    return sum(d) / len(d)


def main():
    points = []
    for label, (f_tr, f_sh, f_pa) in ARMS.items():
        tr, sh, pa = items(f_tr), items(f_sh), items(f_pa)
        content = mean_delta(tr, sh)   # witness content: trace minus shuffle
        fmt = mean_delta(sh, pa)       # format exposure: shuffle minus pair
        share = 100.0 * content / (content + fmt)
        points.append((label, content, fmt, share))
        print(f"{label.replace(chr(10), ' ')}: content {content:+.4f}, "
              f"format {fmt:+.4f}, share {share:.1f}% / {100 - share:.1f}%")

    plt.rcParams.update({"font.size": 9, "axes.edgecolor": "0.3",
                         "axes.linewidth": 0.8})
    fig, ax = plt.subplots(figsize=(4.2, 3.2))

    x = range(len(points))
    width = 0.5
    content_vals = [p[1] for p in points]
    fmt_vals = [p[2] for p in points]

    b1 = ax.bar(x, content_vals, width, color="0.30", edgecolor="black",
                linewidth=0.6, label="content (trace \u2212 shuffle)")
    b2 = ax.bar(x, fmt_vals, width, bottom=content_vals, color="0.80",
                edgecolor="black", linewidth=0.6,
                label="format (shuffle \u2212 pair)")

    for i, (label, content, fmt, share) in enumerate(points):
        ax.text(i, content / 2, f"+{content:.4f}", ha="center", va="center",
                color="white", fontsize=9)
        ax.text(i, content + fmt / 2, f"+{fmt:.4f}", ha="center", va="center",
                color="black", fontsize=9)
        ax.text(i, content + fmt + 0.004,
                f"{share:.0f}% / {100 - share:.0f}%",
                ha="center", va="bottom", fontsize=9)

    ax.set_xticks(list(x))
    ax.set_xticklabels([p[0] for p in points])
    ax.set_ylim(0, 0.10)
    ax.set_ylabel("gap decomposition (sim \u2212 echo)")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        out = OUT_DIR / f"figure7_decomposition.{ext}"
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print("wrote", out)


if __name__ == "__main__":
    main()
