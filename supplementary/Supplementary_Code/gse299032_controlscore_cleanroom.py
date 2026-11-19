# -*- coding: utf-8 -*-
"""GSE299032 mouse heart scRNA: final control-gene module scoring.

This replaces the earlier z-score implementation so that all datasets in the
cross-dataset synthesis use the same primary scoring framework. The dataset has
one control animal, so inference is explicitly directional only.
"""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import sys
import h5py
import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PLANB_ROOT
sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_controlscore_lib import control_module_scores

DATA = ROOT / "02_unpacked" / "GSE299032"
OUT = ROOT / "03_output"
OUT.mkdir(parents=True, exist_ok=True)

SAMPLES = {
    "GSM9031122_F127_Heart_filtered_feature_bc_matrix.h5": ("ICI-model", "F127"),
    "GSM9031128_F1863_Heart_filtered_feature_bc_matrix.h5": ("ICI-model", "F1863"),
    "GSM9031134_F234_Heart_filtered_feature_bc_matrix.h5": ("Control", "F234"),
    "GSM9031140_M1702_Heart_filtered_feature_bc_matrix.h5": ("ICI-model", "M1702"),
    "GSM9876459_558M_Heart_filtered_feature_bc_matrix.h5": ("ICI-model", "558M"),
}

MODULES = {
    "Fibrosis_ECM": ["Col1a1", "Col1a2", "Col3a1", "Col5a1", "Col8a1", "Fn1", "Postn", "Fap", "Tgfb1", "Tgfbr1", "Acta2", "Timp1", "Lox", "Comp", "Thbs1", "Lum", "Dcn"],
    "Inflammation": ["Il6", "Il1b", "Tnf", "Ccl2", "Ccr2", "Cxcl10", "Ifng", "Stat1", "Nfkb1", "Nlrp3", "Cd68", "Lyz2", "Itgam", "Tlr4", "Ccl5", "Il10"],
    "Endothelial": ["Pecam1", "Vwf", "Cdh5", "Kdr", "Flt1", "Angpt2", "Vegfa", "Esm1", "Eng", "Nos3"],
    "Hypoxia_Metabolism": ["Hif1a", "Vegfa", "Slc2a1", "Ldha", "Pgk1", "Eno1", "Hk2", "Pdk1", "Bnip3", "Ndrg1", "Angptl4"],
    "CM_stress": ["Nppa", "Nppb", "Myh7", "Actc1", "Tnnt2", "Ttn", "Myl2", "Pln", "Myh6"],
    "Tcell_cytotoxic": ["Cd3e", "Cd3d", "Cd8a", "Nkg7", "Gzmb", "Prf1", "Ifng", "Ccl5"],
    "Senescence": ["Cdkn1a", "Cdkn2a", "Trp53", "Glb1", "Serpine1", "Il6", "Cxcl8", "Lmnb1"],
}

MARKERS = {
    "Cardiomyocytes": ["Myh6", "Myh7", "Nppa", "Nppb", "Actc1", "Tnnt2", "Ttn"],
    "Fibroblasts": ["Col1a1", "Col1a2", "Dcn", "Postn", "Lum", "Pdgfra", "Col3a1"],
    "Myeloid": ["Cd68", "Lyz2", "Itgam", "Ccr2", "Cd14", "Fcgr1"],
    "T_NK": ["Cd3e", "Cd3d", "Cd8a", "Cd4", "Nkg7", "Gzmb", "Prf1"],
    "Endothelial": ["Pecam1", "Cdh5", "Vwf", "Kdr", "Flt1"],
    "Pericyte_SMC": ["Rgs5", "Pdgfrb", "Acta2", "Myh11", "Des"],
}


def load_h5(path):
    with h5py.File(path, "r") as f:
        g = f["matrix"]
        shape = tuple(int(x) for x in g["shape"][:])  # genes x cells
        data = g["data"][:]
        indices = g["indices"][:]
        indptr = g["indptr"][:]
        genes = [x.decode() if isinstance(x, bytes) else str(x) for x in g["features"]["name"][:]]
        barcodes = [x.decode() if isinstance(x, bytes) else str(x) for x in g["barcodes"][:]]
    X = sp.csc_matrix((data, indices, indptr), shape=shape).T.tocsr()  # cells x genes
    totals = np.asarray(X.sum(axis=1)).ravel()
    keep = totals >= 200
    return X[keep], np.asarray(genes), np.asarray(barcodes)[keep], totals[keep]


cell_frames = []
sample_rows = []
for filename, (group, sample_id) in SAMPLES.items():
    path = DATA / filename
    if not path.exists():
        print("missing", path)
        continue
    X, genes, barcodes, totals = load_h5(path)
    genes_upper = np.array([g.upper() for g in genes])
    scores, controls = control_module_scores(X, genes_upper, MODULES, n_ctrl=10, n_bins=20, seed=42)
    marker_scores, marker_controls = control_module_scores(X, genes_upper, MARKERS, n_ctrl=10, n_bins=20, seed=42)
    celltype = marker_scores.idxmax(axis=1).where(marker_scores.max(axis=1) > 0, "Unassigned")
    frame = pd.DataFrame({
        "sample": sample_id,
        "group": group,
        "cell": barcodes,
        "n_counts": totals,
    })
    frame = pd.concat([frame, scores.reset_index(drop=True)], axis=1)
    frame["celltype"] = celltype.values
    cell_frames.append(frame)
    sample_rows.append({
        "sample": sample_id,
        "group": group,
        "n_cells": len(frame),
        **{m: float(scores[m].mean()) for m in MODULES},
    })
    print(sample_id, group, "kept cells:", len(frame))

cells = pd.concat(cell_frames, ignore_index=True)
cells.to_csv(OUT / "gse299032_controlscore_cells.csv.gz", index=False, compression="gzip")
pb = pd.DataFrame(sample_rows)
pb.to_csv(OUT / "gse299032_controlscore_pseudobulk.csv", index=False)

pbc = cells.groupby(["sample", "group", "celltype"])[list(MODULES)].mean().reset_index()
pbc.to_csv(OUT / "gse299032_controlscore_celltype_pseudobulk.csv", index=False)

summary = []
for module in MODULES:
    for group in ["Control", "ICI-model"]:
        values = cells[cells["group"] == group][module].dropna()
        summary.append({
            "Module": module,
            "Group": group,
            "n_cells": len(values),
            "mean": values.mean(),
            "median": values.median(),
        })
pd.DataFrame(summary).to_csv(OUT / "gse299032_controlscore_summary.csv", index=False)

# Directional differences; with one control animal these are not inferential.
directional = []
control = pb[pb["group"] == "Control"]
ici = pb[pb["group"] == "ICI-model"]
for module in MODULES:
    if len(control) and len(ici):
        directional.append({
            "Dataset": "GSE299032",
            "Species": "mouse",
            "Modality": "scRNA",
            "Comparison": "ICI_vs_Control",
            "Module": module,
            "n_ICI": len(ici),
            "n_Control": len(control),
            "mean_ICI": ici[module].mean(),
            "mean_Control": control[module].mean(),
            "diff": ici[module].mean() - control[module].mean(),
            "inference": "directional_only_single_control",
        })
pd.DataFrame(directional).to_csv(OUT / "gse299032_controlscore_directional.csv", index=False)

print(pb.round(4).to_string(index=False))
print(pd.DataFrame(directional).round(4).to_string(index=False))
