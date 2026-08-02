# Paper source: "When Does the Record of a Computation Matter?"

LaTeX source for the research report (STS-formatted draft).

## Layout

- `main.tex` + `sec_*.tex` — the draft, split one file per section group. Body
  order: intro, formal layer, Parts I–VI, synthesis/methods/limitations.
- `refs.bib` — bibliography (verify every entry by hand before submission; the
  competition requires the reference list to be generated without AI).
- `make_figures.py` — regenerates the four data figures into `figs/`
  (`f3_part2_deltas.pdf`, `f4_budget_curve.pdf`, `f5_ceilings.pdf`,
  `f6_decomposition.pdf`), recomputed from the committed JSON artifacts. The
  two TikZ figures (lens, ZX pipeline) and the provenance chain are inline in
  the `.tex` files.
- `figs/` — the generated figures, committed so the paper builds from a fresh
  clone without running the script first.

The four `\includegraphics` references in the `.tex` files are exactly the four
files the script writes; there are no other image dependencies.

## Build

```bash
python3 make_figures.py            # optional: regenerates ./figs/*.pdf
tectonic main.tex                  # or: pdflatex, two to three passes
```

Requires `matplotlib`, `numpy`, and `scipy` for the figures. No LaTeX toolchain
is installed on the authoring machine, so the PDF is built elsewhere — check
the page count against the cap after any edit that changes length.

Formatting follows the STS research report rules: US letter, 1in margins,
1.5 line spacing, Times-equivalent 11pt body, page numbers bottom right
starting after the abstract, no external links outside the bibliography.

## Not in this directory

- **The plain-language version.** Not committed here. The copy in the
  repository root
  (`../When_Does_the_Record_of_a_Computation_Matter_plain_version.pdf`) is a
  superseded 2026-07-26 snapshot: twelve protocols, no Part VI, no
  verification experiment, and the older companion-repository line counts. Do
  not cite it as current.
