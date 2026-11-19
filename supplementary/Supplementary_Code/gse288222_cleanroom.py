# -*- coding: utf-8 -*-
"""GSE288222 human LV snRNA: final expression-matched control-gene module scores."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
from itertools import combinations
from collections import defaultdict
import gzip
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PLANB_ROOT
DATA = ROOT / "02_unpacked" / "GSE288222"
OUT = ROOT / "03_output"
FIG = ROOT / "04_figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

SAMPLES = {
    "GSM8761493": ("ND", "ND178"), "GSM8761494": ("ND", "ND182"),
    "GSM8761495": ("ND", "ND202"), "GSM8761496": ("ND", "ND236"),
    "GSM8761497": ("ND", "ND245"), "GSM8761498": ("ND", "ND248"),
    "GSM8761499": ("HF", "HF373"), "GSM8761500": ("HF", "HF374"),
    "GSM8761501": ("HF", "HF375"), "GSM8761502": ("HF", "HF378"),
    "GSM8761503": ("HF", "HF379"), "GSM8761504": ("HF", "HF380"),
}
MODULES = {
    "Fibrosis_ECM": ["COL1A1", "COL1A2", "COL3A1", "COL5A1", "COL8A1", "FN1", "POSTN", "FAP", "TGFB1", "TGFBR1", "ACTA2", "TIMP1", "LOX", "COMP", "THBS1", "LUM", "DCN"],
    "Inflammation": ["IL6", "IL1B", "TNF", "CCL2", "CCR2", "CXCL10", "IFNG", "STAT1", "NFKB1", "NLRP3", "CD68", "LYZ", "ITGAM", "TLR4", "CCL5", "IL10"],
    "Endothelial": ["PECAM1", "VWF", "CDH5", "KDR", "FLT1", "ANGPT2", "VEGFA", "ESM1", "ENG", "NOS3"],
    "Hypoxia_Metabolism": ["HIF1A", "VEGFA", "SLC2A1", "LDHA", "PGK1", "ENO1", "HK2", "PDK1", "BNIP3", "NDRG1", "ANGPTL4"],
    "CM_stress": ["NPPA", "NPPB", "MYH7", "ACTC1", "TNNT2", "TTN", "MYL2", "PLN", "MYH6"],
    "Tcell_cytotoxic": ["CD3E", "CD3D", "CD8A", "NKG7", "GZMB", "PRF1", "IFNG", "CCL5"],
    "Senescence": ["CDKN1A", "CDKN2A", "TP53", "GLB1", "SERPINE1", "IL6", "CXCL8", "LMNB1"],
}
MARKERS = {
    "Cardiomyocytes": ["MYH6", "MYH7", "NPPA", "NPPB", "ACTC1", "TNNT2", "TTN"],
    "Fibroblasts": ["COL1A1", "COL1A2", "DCN", "POSTN", "LUM", "PDGFRA", "COL3A1"],
    "Myeloid": ["CD68", "LYZ", "ITGAM", "CCR2", "CD14", "FCGR1A"],
    "T_NK": ["CD3E", "CD3D", "CD8A", "CD4", "NKG7", "GZMB", "PRF1"],
    "Endothelial": ["PECAM1", "CDH5", "VWF", "KDR", "FLT1"],
    "Pericyte_SMC": ["RGS5", "PDGFRB", "ACTA2", "MYH11", "DES"],
}
N_CTRL, N_BINS, SEED = 10, 20, 42


def bh_fdr(p):
    p = np.asarray(p, float)
    out = np.full(len(p), np.nan)
    order = np.argsort(p)
    ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out[order] = np.clip(ranked, 0, 1)
    return out


def exact_perm(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    pool = np.concatenate([a, b])
    n1 = len(a)
    obs = abs(a.mean() - b.mean())
    idx = np.array(list(combinations(range(len(pool)), n1)), dtype=np.int16)
    m1 = pool[idx].mean(axis=1)
    m2 = (pool.sum() - pool[idx].sum(axis=1)) / (len(pool) - n1)
    return obs, ((np.abs(m1 - m2) >= obs - 1e-12).sum() + 1) / (len(idx) + 1)


def first_pass(path):
    gene_sums = defaultdict(float)
    n_cells = None
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t", 7)
            if len(parts) < 8:
                continue
            if parts[0] == "Geneid":
                n_cells = len(parts[7].split("\t"))
                continue
            gene = parts[6].upper()
            vals = np.fromstring(parts[7], sep="\t")
            gene_sums[gene] += float(vals.sum())
    return gene_sums, n_cells


def build_controls(gene_sums, n_cells):
    genes = np.array(sorted(gene_sums))
    means = np.array([gene_sums[g] / n_cells for g in genes], dtype=float)
    order = np.argsort(means)
    bins = np.empty(len(genes), dtype=int)
    bins[order] = np.floor(np.linspace(0, N_BINS - 1, len(genes))).astype(int)
    gene_to_idx = {g: i for i, g in enumerate(genes)}
    rng = np.random.default_rng(SEED)
    controls = {}
    for module, genes_in_module in MODULES.items():
        present = [g for g in genes_in_module if g in gene_to_idx]
        mod_idx = np.array([gene_to_idx[g] for g in present], dtype=int)
        ctrl = []
        ctrl_set = set()
        for gi in mod_idx:
            cand = np.where((bins == bins[gi]) & (~np.isin(np.arange(len(genes)), mod_idx)))[0]
            cand = [int(x) for x in cand if int(x) not in ctrl_set]
            if cand:
                n_pick = min(N_CTRL, len(cand))
                chosen = rng.choice(cand, size=n_pick, replace=False)
                ctrl.extend(int(x) for x in chosen)
                ctrl_set.update(int(x) for x in chosen)
        controls[module] = {
            "module_genes": present,
            "control_genes": [genes[i] for i in ctrl],
        }
    return controls


def second_pass(path, needed_genes):
    values = {}
    totals = None
    cells = None
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t", 7)
            if len(parts) < 8:
                continue
            if parts[0] == "Geneid":
                cells = parts[7].split("\t")
                totals = np.zeros(len(cells), dtype=np.float64)
                continue
            vals = np.fromstring(parts[7], sep="\t")
            totals += vals
            gene = parts[6].upper()
            if gene in needed_genes:
                values[gene] = vals.astype(np.float32)
    return cells, totals, values


all_cells = []
pseudobulk = []
control_records = []
for gsm, (group, sample_id) in SAMPLES.items():
    files = list(DATA.glob(f"{gsm}_matrix_gene_*.tsv.gz"))
    if not files:
        print("missing", gsm)
        continue
    path = files[0]
    gene_sums, n_cells = first_pass(path)
    controls = build_controls(gene_sums, n_cells)
    needed = set(MARKERS and [g for v in MARKERS.values() for g in v])
    needed.update(g for v in MODULES.values() for g in v)
    for mod, info in controls.items():
        needed.update(info["module_genes"])
        needed.update(info["control_genes"])
        for g in info["control_genes"]:
            control_records.append({"GSM": gsm, "Module": mod, "ControlGene": g})
    cells, totals, values = second_pass(path, needed)
    keep = totals >= 200
    score = {}
    for mod, info in controls.items():
        mg = [g for g in info["module_genes"] if g in values]
        cg = [g for g in info["control_genes"] if g in values]
        if len(mg) < 3 or len(cg) < 3:
            score[mod] = np.full(len(cells), np.nan)
            continue
        M = np.vstack([values[g] for g in mg]).astype(float)
        C = np.vstack([values[g] for g in cg]).astype(float)
        ml = np.log1p(M / totals[None, :] * 1e6).mean(axis=0)
        cl = np.log1p(C / totals[None, :] * 1e6).mean(axis=0)
        score[mod] = ml - cl
    marker_score = {}
    for ct, marker_genes in MARKERS.items():
        present = [g for g in marker_genes if g in values]
        if present:
            M = np.vstack([values[g] for g in present]).astype(float)
            marker_score[ct] = np.log1p(M / totals[None, :] * 1e6).mean(axis=0)
        else:
            marker_score[ct] = np.full(len(cells), np.nan)
    marker_df = pd.DataFrame(marker_score)
    celltype = marker_df.idxmax(axis=1).where(marker_df.max(axis=1) > 0, "Unassigned")
    frame = pd.DataFrame({"GSM": gsm, "Group": group, "sample": sample_id, "cell": cells, "n_counts": totals})
    frame = pd.concat([frame, pd.DataFrame(score)], axis=1)
    frame["celltype"] = celltype.values
    frame = frame.loc[keep].reset_index(drop=True)
    all_cells.append(frame)
    pseudobulk.append({"GSM": gsm, "Group": group, "sample": sample_id,
                       **{m: float(np.nanmean(score[m][keep])) for m in MODULES}})
    print(gsm, group, "kept:", int(keep.sum()))

big = pd.concat(all_cells, ignore_index=True)
big.to_csv(OUT / "gse288222_controlscore_cells.csv.gz", index=False, compression="gzip")
pb = pd.DataFrame(pseudobulk)
pb.to_csv(OUT / "gse288222_controlscore_pseudobulk.csv", index=False)
pd.DataFrame(control_records).to_csv(OUT / "gse288222_controlscore_control_genes.csv", index=False)

pbc = big.groupby(["GSM", "Group", "sample", "celltype"])[list(MODULES)].mean().reset_index()
pbc.to_csv(OUT / "gse288222_controlscore_celltype_pseudobulk.csv", index=False)
rows = []
for ct in sorted(pbc["celltype"].unique()):
    for module in MODULES:
        a = pbc[(pbc["celltype"] == ct) & (pbc["Group"] == "HF")][module].dropna().values
        b = pbc[(pbc["celltype"] == ct) & (pbc["Group"] == "ND")][module].dropna().values
        if len(a) < 3 or len(b) < 3:
            continue
        diff, p = exact_perm(a, b)
        rows.append({"CellType": ct, "Module": module, "n_HF": len(a), "n_ND": len(b),
                     "mean_HF": a.mean(), "mean_ND": b.mean(), "diff": a.mean() - b.mean(), "perm_p": p})
res = pd.DataFrame(rows)
res["FDR"] = bh_fdr(res["perm_p"].values)
res.to_csv(OUT / "gse288222_controlscore_celltype_permutation.csv", index=False)

# Sample-level module summary.
sample_res = []
for module in MODULES:
    a = pb[pb["Group"] == "HF"][module].values
    b = pb[pb["Group"] == "ND"][module].values
    diff, p = exact_perm(a, b)
    sample_res.append({"Module": module, "n_HF": len(a), "n_ND": len(b),
                       "mean_HF": a.mean(), "mean_ND": b.mean(), "diff": a.mean() - b.mean(), "perm_p": p})
pd.DataFrame(sample_res).to_csv(OUT / "gse288222_controlscore_sample_permutation.csv", index=False)

# Heatmap of cell-type-resolved differences.
pivot = res.pivot(index="CellType", columns="Module", values="diff")
fig, ax = plt.subplots(figsize=(10, 4.5))
im = ax.imshow(pivot.values, cmap="RdBu_r", vmin=-0.6, vmax=0.6, aspect="auto")
ax.set_xticks(range(len(pivot.columns))); ax.set_xticklabels(pivot.columns, rotation=30, ha="right", fontsize=8)
ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index, fontsize=9)
for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        sub = res[(res["CellType"] == pivot.index[i]) & (res["Module"] == pivot.columns[j])]
        mark = "*" if len(sub) and sub["FDR"].iloc[0] < 0.1 else ""
        ax.text(j, i, f"{pivot.values[i, j]:.2f}{mark}", ha="center", va="center", fontsize=7)
plt.colorbar(im, ax=ax, fraction=0.03, label="HF - ND (module score)")
ax.set_title("GSE288222: cell-type-resolved control-gene module scores")
plt.tight_layout(); plt.savefig(FIG / "GSE288222_controlscore_heatmap.png", dpi=300); plt.close(fig)

print(pb.round(3).to_string(index=False))
print(res.sort_values("perm_p").head(15).round(4).to_string(index=False))
