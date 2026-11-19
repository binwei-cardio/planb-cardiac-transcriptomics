# -*- coding: utf-8 -*-
"""GSE135805 human Spatial Transcriptomics sensitivity scoring.

One section per aetiology; results are descriptive sensitivity evidence only.
"""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import scipy.sparse as sp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = PLANB_ROOT
DATA = ROOT / "01_raw" / "GSE135805"
OUT = ROOT / "03_output"
FIG = ROOT / "04_figures" / "png"
sys.path.insert(0, str(ROOT / "06_scripts"))
from planb_controlscore_lib import control_module_scores

SAMPLES = {
    "GSM4030472_smith2_stdata.tsv.gz": ("Normal", "GSM4030472"),
    "GSM4030473_smith3_stdata.tsv.gz": ("ICM", "GSM4030473"),
    "GSM4030474_smith4_stdata.tsv.gz": ("DCM", "GSM4030474"),
    "GSM4030475_smith5_stdata.tsv.gz": ("HCM", "GSM4030475"),
}
MODULES_SYMBOL = {
    "Fibrosis_ECM": ["COL1A1", "COL1A2", "COL3A1", "COL5A1", "COL8A1", "FN1", "POSTN", "FAP", "TGFB1", "TGFBR1", "ACTA2", "TIMP1", "LOX", "COMP", "THBS1", "LUM", "DCN"],
    "Inflammation": ["IL6", "IL1B", "TNF", "CCL2", "CCR2", "CXCL10", "IFNG", "STAT1", "NFKB1", "NLRP3", "CD68", "LYZ", "ITGAM", "TLR4", "CCL5", "IL10"],
    "Endothelial": ["PECAM1", "VWF", "CDH5", "KDR", "FLT1", "ANGPT2", "VEGFA", "ESM1", "ENG", "NOS3"],
    "Hypoxia_Metabolism": ["HIF1A", "VEGFA", "SLC2A1", "LDHA", "PGK1", "ENO1", "HK2", "PDK1", "BNIP3", "NDRG1", "ANGPTL4"],
    "CM_stress": ["NPPA", "NPPB", "MYH7", "ACTC1", "TNNT2", "TTN", "MYL2", "PLN", "MYH6"],
    "Tcell_cytotoxic": ["CD3E", "CD3D", "CD8A", "NKG7", "GZMB", "PRF1", "IFNG", "CCL5"],
    "Senescence": ["CDKN1A", "CDKN2A", "TP53", "GLB1", "SERPINE1", "IL6", "CXCL8", "LMNB1"],
}
map_df = pd.read_csv(ROOT / "06_scripts" / "resources" / "gene_symbol_to_ensembl.csv")
symbol_to_ens = dict(zip(map_df["symbol"].str.upper(), map_df["ensembl"].str.split(".").str[0]))

all_spots = []
summary = []
coverage = []
for filename, (group, gsm) in SAMPLES.items():
    path = DATA / filename
    if not path.exists():
        print("missing", path)
        continue
    d = pd.read_csv(path, sep="\t", index_col=0)
    d.columns = [str(c).split(".")[0] for c in d.columns]
    d = d.T.groupby(level=0).sum().T
    totals = d.sum(axis=1)
    keep = totals >= 50
    d = d.loc[keep]
    totals = totals.loc[keep]
    module_ids = {}
    for module, symbols in MODULES_SYMBOL.items():
        ids = [symbol_to_ens[s] for s in symbols if s in symbol_to_ens and symbol_to_ens[s] in d.columns]
        module_ids[module] = ids
        coverage.append({"GSM": gsm, "Group": group, "Module": module,
                         "genes_requested": len(symbols), "genes_present": len(ids)})
    scores, controls = control_module_scores(sp.csr_matrix(d.values), list(d.columns), module_ids, n_ctrl=10, n_bins=20, seed=42)
    frame = pd.DataFrame({"GSM": gsm, "Group": group, "spot": d.index})
    frame = pd.concat([frame, scores.reset_index(drop=True)], axis=1)
    frame["n_counts"] = totals.values
    all_spots.append(frame)
    summary.append({"GSM": gsm, "Group": group, "spots_after_QC": len(frame),
                    **{m: float(scores[m].mean()) for m in MODULES_SYMBOL}})
    print(gsm, group, "spots:", len(frame))

spots = pd.concat(all_spots, ignore_index=True)
spots.to_csv(OUT / "gse135805_controlscore_spots.csv.gz", index=False, compression="gzip")
summary_df = pd.DataFrame(summary)
summary_df.to_csv(OUT / "gse135805_controlscore_section_summary.csv", index=False)
pd.DataFrame(coverage).to_csv(OUT / "gse135805_controlscore_gene_coverage.csv", index=False)

# Descriptive section-level heatmap; no inferential statistics because n=1 per group.
mods = list(MODULES_SYMBOL)
mat = summary_df.set_index("Group")[mods].reindex(["Normal", "HCM", "DCM", "ICM"])
fig, ax = plt.subplots(figsize=(7.4, 2.8))
im = ax.imshow(mat.values, cmap="RdBu_r", vmin=-0.8, vmax=0.8, aspect="auto")
ax.set_xticks(range(len(mods))); ax.set_xticklabels(mods, rotation=35, ha="right", fontsize=6)
ax.set_yticks(range(len(mat.index))); ax.set_yticklabels(mat.index, fontsize=7)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        ax.text(j, i, f"{mat.values[i, j]:.2f}", ha="center", va="center", fontsize=5.5)
plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02, label="Module score")
ax.set_title("GSE135805 spatial sensitivity: one section per aetiology", fontsize=9, fontweight="bold")
plt.tight_layout(); plt.savefig(FIG / "GSE135805_controlscore_sections.png", dpi=300, bbox_inches="tight"); plt.close(fig)
print(summary_df.round(3).to_string(index=False))




