# -*- coding: utf-8 -*-
"""Plan B final cross-dataset synthesis v4.

Uses one primary scoring framework (expression-matched control-gene scores)
for all datasets and consistent cell-type/program pairs. Individual dataset
p-values are reported with BH-FDR but cross-dataset direction is the primary
interpretation because sample sizes and platforms differ.
"""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = PLANB_ROOT
OUT = ROOT / "03_output"
FIGPNG = ROOT / "04_figures" / "png"
FIGPDF = ROOT / "04_figures" / "pdf"
FIGTIFF = ROOT / "04_figures" / "tiff"

MODULES = ["Fibrosis_ECM", "Tcell_cytotoxic", "CM_stress", "Inflammation", "Senescence", "Hypoxia_Metabolism"]
PAIR = {
    "Fibrosis_ECM": ("Fibroblasts", "All_spots"),
    "Tcell_cytotoxic": ("T_NK", "All_spots"),
    "CM_stress": ("Cardiomyocytes", "All_spots"),
    "Inflammation": ("Myeloid", "All_spots"),
    "Senescence": ("Cardiomyocytes", "All_cells"),
    "Hypoxia_Metabolism": ("Fibroblasts", "All_spots"),
}
COLUMNS = [
    ("GSE292067", "DoxCM_vs_Donor", "DoxCM vs\nDonor (human)"),
    ("GSE292067", "NICM_vs_Donor", "NICM vs\nDonor (human)"),
    ("GSE288222", "HF_vs_ND", "HF vs ND\n(human)"),
    ("GSE298023", "ICM_vs_Donor", "ICM vs\nDonor (human)"),
    ("GSE298023", "DCM_vs_Donor", "DCM vs\nDonor (human)"),
    ("GSE297745", "ICI_vs_Rescue", "ICI vs Rescue\n(mouse Visium)"),
    ("GSE299032", "ICI_vs_Control", "ICI vs Control\n(mouse scRNA)"),
]


def bh(p):
    p = np.asarray(p, float)
    out = np.full(len(p), np.nan)
    ok = np.isfinite(p)
    if not ok.any():
        return out
    q = p[ok]
    order = np.argsort(q)
    ranked = q[order] * len(q) / np.arange(1, len(q) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    tmp = np.empty(len(q))
    tmp[order] = np.clip(ranked, 0, 1)
    out[np.where(ok)[0]] = tmp
    return out


records = []

# GSE292067: already computed with exact permutation + BH within each contrast.
d = pd.read_csv(OUT / "gse292067_contrast_effects_v2.csv")
for r in d.itertuples(index=False):
    records.append({
        "Dataset": "GSE292067", "Species": "human", "Modality": "snRNA",
        "Comparison": r.Comparison, "CellType": r.CellType, "Module": r.Module,
        "n1": r.n1, "n2": r.n2, "diff": r.diff, "p": r.perm_p, "q": r.FDR,
        "evidence_tier": "human_primary",
    })

# GSE288222: final control-gene scores.
d = pd.read_csv(OUT / "gse288222_controlscore_celltype_permutation.csv")
for r in d.itertuples(index=False):
    records.append({
        "Dataset": "GSE288222", "Species": "human", "Modality": "snRNA",
        "Comparison": "HF_vs_ND", "CellType": r.CellType, "Module": r.Module,
        "n1": r.n_HF, "n2": r.n_ND, "diff": r.diff, "p": r.perm_p, "q": r.FDR,
        "evidence_tier": "human_primary",
    })

# GSE298023: control-gene scores; add BH within each comparison.
d = pd.read_csv(OUT / "gse298023_controlscore_celltype_permutation.csv")
d["q"] = np.nan
for comparison, idx in d.groupby("Comparison").groups.items():
    d.loc[idx, "q"] = bh(d.loc[idx, "perm_p"].values)
d.to_csv(OUT / "gse298023_controlscore_celltype_permutation_with_fdr.csv", index=False)
for r in d.itertuples(index=False):
    records.append({
        "Dataset": "GSE298023", "Species": "human", "Modality": "snRNA",
        "Comparison": r.Comparison, "CellType": r.CellType, "Module": r.Module,
        "n1": r.n1, "n2": r.n2, "diff": r.diff, "p": r.perm_p, "q": r.q,
        "evidence_tier": "human_primary",
    })

# GSE297745: spot-level pseudobulk; BH across modules.
d = pd.read_csv(OUT / "gse297745_controlscore_permutation.csv")
d["q"] = bh(d["perm_p"].values)
d.to_csv(OUT / "gse297745_controlscore_permutation_with_fdr.csv", index=False)
for r in d.itertuples(index=False):
    records.append({
        "Dataset": "GSE297745", "Species": "mouse", "Modality": "Visium",
        "Comparison": "ICI_vs_Rescue", "CellType": "All_spots", "Module": r.Module,
        "n1": 2, "n2": 2, "diff": r.diff, "p": r.perm_p, "q": r.q,
        "evidence_tier": "mouse_supportive",
    })

# GSE299032: only one control animal, so direction only.
d = pd.read_csv(OUT / "gse299032_controlscore_directional.csv")
for r in d.itertuples(index=False):
    records.append({
        "Dataset": "GSE299032", "Species": "mouse", "Modality": "scRNA",
        "Comparison": "ICI_vs_Control", "CellType": "All_cells", "Module": r.Module,
        "n1": r.n_ICI, "n2": r.n_Control, "diff": r.diff, "p": np.nan, "q": np.nan,
        "evidence_tier": "mouse_directional_only",
    })

master = pd.DataFrame(records)
master.to_csv(OUT / "planb_master_module_tests_v4.csv", index=False)

# Build the matrix with consistent cell-type/program pairs.
values = pd.DataFrame(index=MODULES, columns=[c[2] for c in COLUMNS], dtype=float)
qvalues = pd.DataFrame(index=MODULES, columns=[c[2] for c in COLUMNS], dtype=float)
tier = pd.DataFrame(index=MODULES, columns=[c[2] for c in COLUMNS], dtype=object)
for module in MODULES:
    for dataset, comparison, label in COLUMNS:
        cell_type = PAIR[module][0]
        if dataset == "GSE297745":
            cell_type = "All_spots"
        elif dataset == "GSE299032":
            cell_type = "All_cells"
        rec = master[(master.Dataset == dataset) & (master.Comparison == comparison) &
                     (master.CellType == cell_type) & (master.Module == module)]
        if len(rec):
            values.loc[module, label] = rec["diff"].iloc[0]
            qvalues.loc[module, label] = rec["q"].iloc[0]
            tier.loc[module, label] = rec["evidence_tier"].iloc[0]

values.to_csv(OUT / "planb_cross_dataset_matrix_v4.csv")
qvalues.to_csv(OUT / "planb_cross_dataset_qvalues_v4.csv")
tier.to_csv(OUT / "planb_cross_dataset_evidence_tier_v4.csv")

# Direction heatmap with transparent significance labels.
fig, ax = plt.subplots(figsize=(12.5, 5.8))
im = ax.imshow(values.values, cmap="RdBu_r", vmin=-0.8, vmax=0.8, aspect="auto")
ax.set_xticks(range(values.shape[1])); ax.set_xticklabels(values.columns, rotation=0, ha="center", fontsize=7)
ax.set_yticks(range(values.shape[0])); ax.set_yticklabels(values.index, fontsize=9)
for i in range(values.shape[0]):
    for j in range(values.shape[1]):
        val = values.values[i, j]
        if np.isnan(val):
            ax.text(j, i, "NA", ha="center", va="center", fontsize=7, color="#777777")
            continue
        q = qvalues.values[i, j]
        if np.isfinite(q) and q < 0.05:
            mark = "**"
        elif np.isfinite(q) and q < 0.10:
            mark = "*"
        elif np.isfinite(q):
            mark = "†"
        else:
            mark = "d"
        ax.text(j, i, f"{val:.2f}{mark}", ha="center", va="center", fontsize=7.5)
ax.set_title("Cross-dataset module differences using the final control-gene scoring framework", fontsize=11, fontweight="bold")
cb = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cb.set_label("Disease/cardiotoxicity - control (module score)", fontsize=8)
ax.text(0, 1.02, "**FDR<0.05; *FDR<0.10; †nominal p<0.05; d=directional only (single control)",
        transform=ax.transAxes, fontsize=8, va="bottom")
plt.tight_layout()
plt.savefig(FIGPNG / "PlanB_cross_dataset_programs_v4.png", dpi=300, bbox_inches="tight")
plt.savefig(FIGPDF / "PlanB_cross_dataset_programs_v4.pdf", bbox_inches="tight")
plt.savefig(FIGTIFF / "PlanB_cross_dataset_programs_v4.tiff", dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
plt.close(fig)

print(values.round(3).to_string())
print("\nQ values:")
print(qvalues.round(3).to_string())
print("\nDirection summary for consistent pairs:")
for module in MODULES:
    x = values.loc[module].dropna()
    print(module, "n=", len(x), "positive=", int((x > 0).sum()), "negative=", int((x < 0).sum()))
print("\nwrote:", OUT / "planb_master_module_tests_v4.csv")

