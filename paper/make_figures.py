#!/usr/bin/env python3
"""Regenerate all data figures for the research report from the committed numbers.
Usage: python3 make_figures.py   (outputs PDFs into ./figs/)
All numbers trace to committed artifacts in the project repository
(see verify.py and the results/ directories there).
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figs')
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    'font.size': 10, 'axes.labelsize': 10,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.dpi': 200, 'savefig.bbox': 'tight'
})
C1, C2, C3 = '#2c6fbb', '#c44e52', '#555555'

# ---------- F3: Part II deltas (panel a) + drift (panel b) ----------
pairs   = ['mod_mult_55', 'mod5_4', 'barenco\ntof_3', 'tof_3\n(control)']
delta   = [0.0670, 0.0248, 0.0167, -0.0042]
z       = [9.5, 4.8, 3.9, -1.1]
pred    = [0.029, 0.048, 0.020, 0.013]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.1), gridspec_kw={'width_ratios': [1.2, 1.0]})

x = np.arange(4)
cols = [C1, C1, C1, '#b0b0b0']
ax1.bar(x, delta, width=0.56, color=cols, zorder=3)
ax1.scatter(x, pred, marker='D', facecolor='none', edgecolor=C2, s=46, lw=1.5,
            zorder=4, label='registered prediction\n(1% depolarizing model)')
for xi, d, zi in zip(x, delta, z):
    if d >= 0:
        ax1.text(xi, d - 0.006, f'{d:+.4f}', ha='center', va='top',
                 fontsize=8.5, color='white', fontweight='bold')
        ax1.text(xi, max(d, pred[list(x).index(xi)]) + 0.006, f'z = {zi:+.1f}',
                 ha='center', fontsize=7.5, color='#666666')
    else:
        ax1.text(xi, d - 0.007, f'{d:+.4f}', ha='center', fontsize=8.5)
        ax1.text(xi, d - 0.015, f'z = {zi:+.1f}', ha='center', fontsize=7.5, color='#666666')
ax1.axhline(0, color='k', lw=0.7)
ax1.set_xticks(x); ax1.set_xticklabels(pairs, fontsize=8.5)
ax1.set_ylabel(r'$\Delta$ fidelity (optimized $-$ baseline)')
ax1.set_ylim(-0.032, 0.095)
ax1.legend(frameon=False, fontsize=8, loc='upper right')
ax1.set_title('(a) one interleaved job per pair, 8192 shots', fontsize=9.5, pad=6)

circuits = ['mod5_4', 'tof_3', 'barenco', 'mod_mult']
t1 = [0.532, 0.531, 0.509, 0.267]
t2 = [0.620, 0.692, 0.595, 0.270]
dy = [0.008, 0.004, -0.010, 0.0]
pc = [C1, C2, '#4c9f70', '#8c6bb1']
for i, (a, b) in enumerate(zip(t1, t2)):
    ax2.plot([0, 1], [a, b], '-o', color=pc[i], ms=4, lw=1.5)
    ax2.text(1.06, b + dy[i], f'{circuits[i]}  ({b - a:+.3f})', va='center', fontsize=8, color=pc[i])
ax2.set_xlim(-0.15, 1.9)
ax2.set_xticks([0, 1]); ax2.set_xticklabels(['13:25', '18:52'], fontsize=8.5)
ax2.set_ylabel('fidelity')
ax2.set_ylim(0.2, 0.76)
ax2.set_title('(b) drift: same circuits, 5.5 h apart', fontsize=9.5, pad=6)

fig.tight_layout(w_pad=2.0)
fig.savefig(os.path.join(FIG, 'f3_part2_deltas.pdf')); plt.close(fig)

# ---------- F4: Part V budget curve ----------
N     = np.array([125, 250, 500, 1000, 2000, 4000])
trace = [-0.0736, -0.0699, -0.0715, -0.0573, -0.0718, -0.0427]
pair  = [-0.1823, -0.1483, -0.1397, -0.1302, -0.1245, -0.1256]
gap   = [0.1086, 0.0784, 0.0682, 0.0729, 0.0527, 0.0829]
lx = np.log2(N)

fig, ax = plt.subplots(figsize=(6.6, 3.6))
ax.plot(lx, trace, 'o-', color=C1, lw=1.6, ms=5, label='pw_trace')
ax.plot(lx, pair, 's-', color=C2, lw=1.6, ms=5, label='pw_pair')
ax.plot(lx, gap, 'D--', color=C3, lw=1.4, ms=4.5, label='gap (trace - pair)')
ax.axhline(0, color='k', lw=0.6, alpha=0.4)
for xx, g in zip(lx, gap):
    ax.annotate(f'+{g:.4f}', (xx, g), textcoords='offset points', xytext=(0, 7),
                ha='center', fontsize=8, color=C3)
ax.annotate('Part III anchor\n+0.054 at seed 0', xy=(np.log2(2000), 0.0527),
            xytext=(np.log2(2000) + 0.25, 0.012), fontsize=8.5, color='#333333',
            arrowprops=dict(arrowstyle='->', lw=0.7, color='#333333'))
ax.set_xticks(lx); ax.set_xticklabels([str(n) for n in N])
ax.set_xlabel('stage-2 budget $N$ (examples, log$_2$ scale)')
ax.set_ylabel('sim $-$ echo')
ax.set_ylim(-0.205, 0.145)
ax.legend(frameon=False, fontsize=9, loc='lower left')
fig.savefig(os.path.join(FIG, 'f4_budget_curve.pdf')); plt.close(fig)

# ---------- F5: Bayes ceilings ----------
conds  = ['readable', 'free', 'q25', 'q50', 'q75', 'abelian']
ceil   = [1.000, 1.000, 0.915, 0.739, 0.514, 0.190]
fibers = ['1.0', '1.0', '2.8', '29.7', '349.1', '2581.0']
chance = 0.125

fig, ax = plt.subplots(figsize=(6.6, 3.8))
x = np.arange(6)
cols = ['#4c9f70', '#4c9f70', C1, C1, C1, C2]
ax.bar(x, ceil, width=0.58, color=cols, zorder=3)
ax.axhline(chance, color='k', lw=1.0, ls='--', zorder=4)
ax.text(-0.45, chance + 0.025, 'chance = 0.125', fontsize=9,
        bbox=dict(facecolor='white', edgecolor='none', pad=1.2))
for xi, c in zip(x, ceil):
    ax.text(xi, c + 0.022, f'{c:.3f}', ha='center', fontsize=9.5)
ax.annotate('', xy=(4.62, chance), xytext=(4.62, 0.190),
            arrowprops=dict(arrowstyle='<->', lw=1.0, color='#333333'))
ax.text(4.52, 0.155, 'max gap = 0.065', fontsize=8.5, va='center', ha='right',
        bbox=dict(facecolor='white', edgecolor='none', pad=1.2))
ax.set_xticks(x)
ax.set_xticklabels([f'{c}\n fiber {f}' for c, f in zip(conds, fibers)], fontsize=8.2)
ax.tick_params(axis='x', pad=2)
ax.set_ylabel('Bayes ceiling (token accuracy)')
ax.set_ylim(0, 1.10)
ax.set_xlim(-0.6, 5.75)
fig.savefig(os.path.join(FIG, 'f5_ceilings.pdf')); plt.close(fig)

# ---------- F6: content/format decomposition ----------
fig, ax = plt.subplots(figsize=(4.6, 3.2))
groups  = ['Part III\n($N$ = 2000)', 'Part V\n($N$ = 4000)']
content = [0.0393, 0.0563]
format_ = [0.0146, 0.0266]
x = np.arange(2)
ax.bar(x, content, width=0.45, color=C1, label='content (trace - shuffle)')
ax.bar(x, format_, width=0.45, bottom=content, color='#e0a458', label='format (shuffle - pair)')
for xi, (c, f) in enumerate(zip(content, format_)):
    tot = c + f
    ax.text(xi, c/2, f'{c:+.4f}', ha='center', va='center', fontsize=8.5, color='white')
    ax.text(xi, c + f/2, f'{f:+.4f}', ha='center', va='center', fontsize=8.5, color='black')
    ax.text(xi, tot + 0.004, f'{100*c/tot:.0f}% / {100*f/tot:.0f}%',
            ha='center', fontsize=9, fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(groups, fontsize=9)
ax.set_ylabel('gap decomposition (sim $-$ echo)')
ax.set_ylim(0, 0.105)
ax.legend(frameon=False, fontsize=8, loc='upper left')
fig.savefig(os.path.join(FIG, 'f6_decomposition.pdf')); plt.close(fig)

print('figures written to', FIG)
