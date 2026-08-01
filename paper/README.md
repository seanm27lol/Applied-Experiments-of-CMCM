# Paper source: "When Does the Record of a Computation Matter?"

LaTeX source for the research report (STS-formatted draft) and the plain-language
version. Both compile to exactly 20 counted body pages (title, abstract, and
bibliography excluded from the cap).

## Layout

- `main.tex` + `sec_*.tex` — the main draft, split one file per section group.
- `refs.bib` — bibliography (verify every entry before submission; the
  competition requires the reference list to be generated without AI).
- `make_figures.py` — regenerates the four data figures into `figs/`
  (`f3_part2_deltas.pdf`, `f4_budget_curve.pdf`, `f5_ceilings.pdf`,
  `f6_decomposition.pdf`). The two TikZ figures (lens, ZX pipeline) and the
  provenance chain are inline in the `.tex` files. Note: the Figure 7 currently
  in the paper is the author's regenerated grayscale version
  (`figure7_decomposition.pdf`, recomputed from the committed JSONs); the script
  keeps the older colored variant for reference.
- `plain/` — the plain-language version (same numbers, tables, structure,
  simpler prose). Source available on request.

## Build

```bash
python3 make_figures.py            # writes ./figs/*.pdf
tectonic main.tex                  # or: pdflatex, two to three passes
```

Formatting follows the STS research report rules: US letter, 1in margins,
1.5 line spacing, Times-equivalent 11pt body, page numbers bottom right
starting after the abstract, no external links outside the bibliography.
