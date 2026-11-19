# -*- coding: utf-8 -*-
"""GSE161470 sensitivity analysis using expression-matched control-gene scores."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
from collections import defaultdict
import gzip
import re
import numpy as np
import pandas as pd

import sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PLANB_ROOT
DATA = ROOT / "01_raw" / "GSE161470"
OUT = ROOT / "03_output"
OUT.mkdir(parents=True, exist_ok=True)
N_CTRL, N_BINS, SEED = 10, 20, 42

FILES = {
    "Control": DATA / "GSE161470_cell.counts.Control.txt.gz",
    "HF": DATA / "GSE161470_cell.counts.HF.txt.gz",
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


def first_pass(path):
    sums = defaultdict(float)
    n_cells = None
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        header = f.readline().strip().split()
        n_cells = len(header)
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            gene = parts[0].strip('"').upper()
            vals = np.array(parts[1:], dtype=float)
            if len(vals) != n_cells:
                continue
            sums[gene] += float(vals.sum())
    means = {g: sums[g] / n_cells for g in sums}
    return means, n_cells


def build_controls(means):
    genes = np.array(sorted(means))
    values = np.array([means[g] for g in genes])
    order = np.argsort(values)
    bins = np.empty(len(genes), dtype=int)
    bins[order] = np.floor(np.linspace(0, N_BINS - 1, len(genes))).astype(int)
    g2i = {g: i for i, g in enumerate(genes)}
    rng = np.random.default_rng(SEED)
    out = {}
    for module, symbols in MODULES.items():
        mod = [g for g in symbols if g in g2i]
        mod_idx = np.array([g2i[g] for g in mod], dtype=int)
        ctrl = []
        seen = set()
        for gi in mod_idx:
            cand = np.where((bins == bins[gi]) & (~np.isin(np.arange(len(genes)), mod_idx)))[0]
            cand = [int(i) for i in cand if int(i) not in seen]
            if cand:
                pick = rng.choice(cand, size=min(N_CTRL, len(cand)), replace=False)
                ctrl.extend(int(i) for i in pick)
                seen.update(int(i) for i in pick)
        out[module] = (mod, [genes[i] for i in ctrl])
    return out


def second_pass(path, needed):
    values = {}
    totals = None
    cells = None
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        header = f.readline().strip().split()
        cells = [re.sub(r'\.(\d+)_', r'-\1_', x.strip('"')) for x in header]
        totals = np.zeros(len(cells), dtype=float)
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            gene = parts[0].strip('"').upper()
            vals = np.array(parts[1:], dtype=float)
            if len(vals) != len(totals):
                continue
            totals += vals
            if gene in needed:
                values[gene] = vals.astype(np.float32)
    return cells, totals, values


frames = []
for group, path in FILES.items():
    means, n_cells = first_pass(path)
    controls = build_controls(means)
    needed = set(g for v in MODULES.values() for g in v) | set(g for v in MARKERS.values() for g in v)
    for module, (mod, ctrl) in controls.items():
        needed.update(mod); needed.update(ctrl)
    cells, totals, values = second_pass(path, needed)
    keep = totals >= 200
    score = {}
    for module, (mod, ctrl) in controls.items():
        mod = [g for g in mod if g in values]
        ctrl = [g for g in ctrl if g in values]
        if len(mod) < 3 or len(ctrl) < 3:
            score[module] = np.full(len(cells), np.nan); continue
        M = np.vstack([values[g] for g in mod]).astype(float)
        C = np.vstack([values[g] for g in ctrl]).astype(float)
        score[module] = np.log1p(M / totals[None, :] * 1e6).mean(axis=0) - np.log1p(C / totals[None, :] * 1e6).mean(axis=0)
    marker = {}
    for ct, symbols in MARKERS.items():
        present = [g for g in symbols if g in values]
        if present:
            M = np.vstack([values[g] for g in present]).astype(float)
            marker[ct] = np.log1p(M / totals[None, :] * 1e6).mean(axis=0)
        else:
            marker[ct] = np.full(len(cells), np.nan)
    mdf = pd.DataFrame(marker)
    arr = mdf.to_numpy(dtype=float, copy=True)
    arr[~np.isfinite(arr)] = -np.inf
    best = arr.argmax(axis=1)
    best_val = arr[np.arange(len(arr)), best]
    celltype = pd.Series(np.where(np.isfinite(best_val), mdf.columns[best], "Unassigned"), index=mdf.index)
    frame = pd.DataFrame({"Group": group, "cell": cells, "n_counts": totals, "celltype": celltype.values})
    frame = pd.concat([frame, pd.DataFrame(score)], axis=1).loc[keep].reset_index(drop=True)
    frames.append(frame)
    print(group, "kept cells:", len(frame))

big = pd.concat(frames, ignore_index=True)
big.to_csv(OUT / "gse161470_controlscore_cells.csv.gz", index=False, compression="gzip")
pbs = big.groupby(["Group", "celltype"])[list(MODULES)].mean().reset_index()
pbs.to_csv(OUT / "gse161470_controlscore_pseudobulk_celltype.csv", index=False)
summary = []
for ct in sorted(pbs.celltype.unique()):
    for module in MODULES:
        a = pbs[(pbs.Group == "HF") & (pbs.celltype == ct)][module]
        b = pbs[(pbs.Group == "Control") & (pbs.celltype == ct)][module]
        if len(a) and len(b):
            summary.append({"CellType": ct, "Module": module, "n_HF": len(a), "n_Control": len(b),
                            "mean_HF": float(a.mean()), "mean_Control": float(b.mean()), "diff": float(a.mean() - b.mean())})
pd.DataFrame(summary).to_csv(OUT / "gse161470_controlscore_celltype_directional.csv", index=False)
print(pbs.round(3).to_string(index=False))





