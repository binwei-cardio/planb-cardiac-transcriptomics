# -*- coding: utf-8 -*-
"""GSE292067 group contrasts and specificity analysis.

Inputs:
  output/gse292067_pseudobulk_celltype.csv
Outputs:
  output/gse292067_contrast_effects_v2.csv
  output/gse292067_global_group_tests_v2.csv
  figures/GSE292067_contrasts_v2.png/.pdf
"""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
from itertools import combinations
import numpy as np
import pandas as pd
from scipy.stats import kruskal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = PLANB_ROOT
OUT = ROOT / "03_output"
FIGPNG = ROOT / "04_figures" / "png"
FIGPDF = ROOT / "04_figures" / "pdf"
FIGTIFF = ROOT / "04_figures" / "tiff"
OUT.mkdir(exist_ok=True)
FIGPNG.mkdir(parents=True, exist_ok=True)
FIGPDF.mkdir(parents=True, exist_ok=True)
FIGTIFF.mkdir(parents=True, exist_ok=True)

modules = ["Fibrosis_ECM", "Inflammation", "Endothelial", "Hypoxia_Metabolism",
           "CM_stress", "Tcell_cytotoxic", "Senescence"]
comparisons = [
    ("DoxCM", "Donor", "DoxCM_vs_Donor"),
    ("NICM", "Donor", "NICM_vs_Donor"),
    ("DoxCM", "NICM", "DoxCM_vs_NICM"),
]
group_order = ["Donor", "DoxCM", "NICM"]
group_colors = {"Donor": "#4C78A8", "DoxCM": "#E45756", "NICM": "#59A14F"}

pb = pd.read_csv(OUT / "gse292067_pseudobulk_celltype.csv")


def bh_fdr(p):
    p = np.asarray(p, float)
    out = np.full(len(p), np.nan)
    ok = np.isfinite(p)
    if not ok.any():
        return out
    q = p[ok]
    order = np.argsort(q)
    ranked = q[order] * len(q) / np.arange(1, len(q) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    tmp = np.empty(len(q), float)
    tmp[order] = np.clip(ranked, 0, 1)
    out[np.where(ok)[0]] = tmp
    return out


def exact_perm_mean(a, b, cache):
    """Two-sided exact permutation p for difference in means."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    n1, n2 = len(a), len(b)
    key = (n1, n2)
    pool = np.concatenate([a, b])
    if key not in cache:
        pool_n = n1 + n2
        idx = np.array(list(combinations(range(pool_n), n1)), dtype=np.int16)
        cache[key] = idx
    idx = cache[key]
    combo_sums = pool[idx].sum(axis=1)
    total = pool.sum()
    mean1 = combo_sums / n1
    mean2 = (total - combo_sums) / n2
    null_abs = np.abs(mean1 - mean2)
    obs = abs(a.mean() - b.mean())
    p = (np.count_nonzero(null_abs >= obs - 1e-12) + 1) / (len(null_abs) + 1)
    return obs, p


def hedges_g(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return np.nan
    sp2 = (((n1 - 1) * a.var(ddof=1)) + ((n2 - 1) * b.var(ddof=1))) / (n1 + n2 - 2)
    if sp2 <= 0:
        return 0.0
    d = (a.mean() - b.mean()) / np.sqrt(sp2)
    correction = 1 - (3 / (4 * (n1 + n2) - 9))
    return correction * d


def cliffs_delta(a, b):
    a = np.asarray(a, float)[:, None]
    b = np.asarray(b, float)[None, :]
    return float((a > b).mean() - (a < b).mean())


def bootstrap_diff_ci(a, b, n_boot=20000, seed=42):
    rng = np.random.default_rng(seed)
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    x = rng.choice(a, size=(n_boot, len(a)), replace=True).mean(axis=1)
    y = rng.choice(b, size=(n_boot, len(b)), replace=True).mean(axis=1)
    d = x - y
    return np.quantile(d, [0.025, 0.5, 0.975])


cache = {}
rows = []
for ct in sorted(pb["celltype"].unique()):
    for module in modules:
        for g1, g2, label in comparisons:
            a = pb[(pb["celltype"] == ct) & (pb["Group"] == g1)][module].dropna().values
            b = pb[(pb["celltype"] == ct) & (pb["Group"] == g2)][module].dropna().values
            if len(a) < 3 or len(b) < 3:
                continue
            diff, p = exact_perm_mean(a, b, cache)
            ci_low, ci_med, ci_high = bootstrap_diff_ci(a, b, seed=20260913 + len(rows))
            rows.append({
                "CellType": ct,
                "Module": module,
                "Comparison": label,
                "Group1": g1,
                "Group2": g2,
                "n1": len(a),
                "n2": len(b),
                "mean1": a.mean(),
                "mean2": b.mean(),
                "diff": a.mean() - b.mean(),
                "hedges_g": hedges_g(a, b),
                "cliffs_delta": cliffs_delta(a, b),
                "boot_ci_low": ci_low,
                "boot_ci_high": ci_high,
                "perm_p": p,
            })

eff = pd.DataFrame(rows)
eff["FDR"] = np.nan
for _, idx in eff.groupby("Comparison").groups.items():
    eff.loc[idx, "FDR"] = bh_fdr(eff.loc[idx, "perm_p"].values)
eff = eff.sort_values(["Comparison", "FDR", "perm_p", "CellType", "Module"]).reset_index(drop=True)
eff.to_csv(OUT / "gse292067_contrast_effects_v2.csv", index=False)

# Three-group global tests (Kruskal-Wallis; BH across cell type x module tests).
global_rows = []
for ct in sorted(pb["celltype"].unique()):
    for module in modules:
        groups = [g[module].dropna().values for _, g in pb[pb["celltype"] == ct].groupby("Group")]
        groups = [x for x in groups if len(x) >= 3]
        if len(groups) < 3:
            continue
        stat, p = kruskal(*groups)
        global_rows.append({
            "CellType": ct,
            "Module": module,
            "Groups": ";".join(f"n={len(x)}" for x in groups),
            "Kruskal_H": stat,
            "perm_or_asymptotic_p": p,
        })
gl = pd.DataFrame(global_rows)
gl["FDR"] = bh_fdr(gl["perm_or_asymptotic_p"].values)
gl = gl.sort_values(["FDR", "perm_or_asymptotic_p"]).reset_index(drop=True)
gl.to_csv(OUT / "gse292067_global_group_tests_v2.csv", index=False)

# Compact specificity table using the two disease groups versus donor and the direct contrast.
wide = eff.pivot_table(
    index=["CellType", "Module"], columns="Comparison",
    values=["diff", "perm_p", "FDR", "hedges_g"], aggfunc="first"
)
wide.columns = [f"{a}_{b}" for a, b in wide.columns]
wide = wide.reset_index()
wide.to_csv(OUT / "gse292067_specificity_matrix_v2.csv", index=False)

# Figure: selected programs, group distributions, and DoxCM_vs_NICM effects.
selected = [
    ("Cardiomyocytes", "Senescence"),
    ("Fibroblasts", "Fibrosis_ECM"),
    ("Endothelial", "Fibrosis_ECM"),
    ("Endothelial", "Inflammation"),
    ("Endothelial", "Senescence"),
    ("T_NK", "Tcell_cytotoxic"),
]
fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
axes = axes.ravel()

# Panels A-E: group distributions for five interpretable programmes.
for ax, (ct, module), panel in zip(
    axes[:5], selected[:5], ["A", "B", "C", "D", "E"]
):
    sub = pb[(pb["celltype"] == ct) & (pb["Group"].isin(group_order))]
    data = [sub[sub["Group"] == g][module].dropna().values for g in group_order]
    bp = ax.boxplot(
        data, patch_artist=True, widths=0.62, showfliers=False,
        medianprops={"color": "black", "linewidth": 1.2},
    )
    for patch, g in zip(bp["boxes"], group_order):
        patch.set_facecolor(group_colors[g])
        patch.set_alpha(0.42)
    rng = np.random.default_rng(7)
    for i, (g, vals) in enumerate(zip(group_order, data), start=1):
        ax.scatter(
            np.full(len(vals), i) + rng.normal(0, 0.045, len(vals)),
            vals, s=22, color=group_colors[g], edgecolor="white",
            linewidth=0.4, zorder=3,
        )
    q = gl[(gl.CellType == ct) & (gl.Module == module)]
    qtxt = f"global FDR={q.FDR.iloc[0]:.3f}" if len(q) else ""
    ax.set_title(f"{panel}. {ct}: {module}" + chr(10) + qtxt, fontsize=10, fontweight="bold", loc="left")
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(group_order)
    ax.axhline(0, color="grey", lw=0.6, ls=":")
    ax.set_ylabel("Control-gene module score")
    ax.spines[["top", "right"]].set_visible(False)

# Panel F: direct DoxCM-vs-NICM effects. No direct contrast survived FDR.
forest_ax = axes[5]
cur = eff[eff.Comparison == "DoxCM_vs_NICM"].copy()
cur["label"] = cur["CellType"] + " / " + cur["Module"]
# Show the 12 lowest nominal p-values to keep the forest plot legible; the
# complete 42-combination result remains in the source table.
cur = cur.sort_values("perm_p").head(12).sort_values("diff")
y = np.arange(len(cur))
forest_ax.errorbar(
    cur["diff"], y,
    xerr=np.vstack([
        cur["diff"] - cur["boot_ci_low"],
        cur["boot_ci_high"] - cur["diff"],
    ]),
    fmt="o", ms=4, color="#6A3D9A", ecolor="#B8A6D9",
    elinewidth=1, capsize=0,
)
forest_ax.axvline(0, color="black", lw=0.8, ls="--")
forest_ax.set_yticks(y)
forest_ax.set_yticklabels(cur["label"], fontsize=6.5)
forest_ax.set_xlabel("DoxCM - NICM (module score; 95% bootstrap CI)", fontsize=8)
forest_ax.set_title("F. Direct contrast: DoxCM vs NICM", fontsize=10, fontweight="bold", loc="left")
forest_ax.spines[["top", "right"]].set_visible(False)

note = (
    "No direct DoxCM-vs-NICM contrast survived BH-FDR. Nominal trends are exploratory "
    "and should not be interpreted as chemotherapy-specific."
)
fig.suptitle(
    "GSE292067: donor, doxorubicin cardiomyopathy (DoxCM), and non-ischaemic cardiomyopathy (NICM)",
    fontsize=14, fontweight="bold",
)
fig.text(0.5, -0.01, note, ha="center", fontsize=9, color="#7A1F1F")
fig.savefig(FIGPNG / "GSE292067_contrasts_v2.png", dpi=300, bbox_inches="tight")
fig.savefig(FIGPDF / "GSE292067_contrasts_v2.pdf", bbox_inches="tight")
fig.savefig(FIGTIFF / "GSE292067_contrasts_v2.tiff", dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
plt.close(fig)


print("wrote", OUT / "gse292067_contrast_effects_v2.csv")
print("wrote", OUT / "gse292067_global_group_tests_v2.csv")
print("wrote", OUT / "gse292067_specificity_matrix_v2.csv")
print("wrote", FIGPNG / "GSE292067_contrasts_v2.png")
print("\nGlobal FDR < 0.10:")
print(gl[gl.FDR < 0.10].to_string(index=False))
print("\nDoxCM vs NICM, lowest p:")
print(eff[eff.Comparison == "DoxCM_vs_NICM"].head(12).to_string(index=False))





