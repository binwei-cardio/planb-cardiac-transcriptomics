# -*- coding: utf-8 -*-
"""Primary biological pair summary across datasets (four interpretable pairs)."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = PLANB_ROOT
OUT = ROOT / "03_output"


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
    tmp = np.empty(len(q)); tmp[order] = np.clip(ranked, 0, 1)
    out[np.where(ok)[0]] = tmp
    return out

pairs = [
    ("Fibroblasts", "Fibrosis_ECM", "Fibroblast fibrosis-ECM"),
    ("T_NK", "Tcell_cytotoxic", "T/NK cytotoxic"),
    ("Cardiomyocytes", "CM_stress", "Cardiomyocyte stress"),
    ("Myeloid", "Inflammation", "Myeloid inflammation"),
]
rows = []

# GSE292067
d = pd.read_csv(OUT / "gse292067_contrast_effects_v2.csv")
for comparison, label in [("DoxCM_vs_Donor", "DoxCM vs Donor"), ("NICM_vs_Donor", "NICM vs Donor"), ("DoxCM_vs_NICM", "DoxCM vs NICM")]:
    sub = d[d.Comparison == comparison].copy()
    for ct, module, name in pairs:
        r = sub[(sub.CellType == ct) & (sub.Module == module)]
        if len(r):
            rows.append({"Dataset": "GSE292067", "Species": "human", "Modality": "snRNA", "Comparison": label,
                         "Pair": name, "CellType": ct, "Module": module, "n1": int(r.n1.iloc[0]), "n2": int(r.n2.iloc[0]),
                         "diff": float(r["diff"].iloc[0]), "p": float(r.perm_p.iloc[0]), "source_q": float(r.FDR.iloc[0])})

# GSE288222
d = pd.read_csv(OUT / "gse288222_controlscore_celltype_permutation.csv")
for ct, module, name in pairs:
    r = d[(d.CellType == ct) & (d.Module == module)]
    if len(r):
        rows.append({"Dataset": "GSE288222", "Species": "human", "Modality": "snRNA", "Comparison": "HF vs ND",
                     "Pair": name, "CellType": ct, "Module": module, "n1": int(r.n_HF.iloc[0]), "n2": int(r.n_ND.iloc[0]),
                     "diff": float(r["diff"].iloc[0]), "p": float(r.perm_p.iloc[0]), "source_q": float(r.FDR.iloc[0])})

# GSE298023
d = pd.read_csv(OUT / "gse298023_controlscore_celltype_permutation_with_fdr.csv")
for comparison, label in [("ICM_vs_Donor", "ICM vs Donor"), ("DCM_vs_Donor", "DCM vs Donor")]:
    sub = d[d.Comparison == comparison].copy()
    for ct, module, name in pairs:
        r = sub[(sub.CellType == ct) & (sub.Module == module)]
        if len(r):
            rows.append({"Dataset": "GSE298023", "Species": "human", "Modality": "snRNA", "Comparison": label,
                         "Pair": name, "CellType": ct, "Module": module, "n1": int(r.n1.iloc[0]), "n2": int(r.n2.iloc[0]),
                         "diff": float(r["diff"].iloc[0]), "p": float(r.perm_p.iloc[0]), "source_q": float(r.q.iloc[0])})

# GSE297745: spatial module score only; use all-spot programmes.
d = pd.read_csv(OUT / "gse297745_controlscore_permutation_with_fdr.csv")
for module, name in [("Fibrosis_ECM", "Fibroblast fibrosis-ECM"), ("Tcell_cytotoxic", "T/NK cytotoxic"),
                     ("CM_stress", "Cardiomyocyte stress"), ("Inflammation", "Myeloid inflammation")]:
    r = d[d.Module == module]
    if len(r):
        rows.append({"Dataset": "GSE297745", "Species": "mouse", "Modality": "Visium", "Comparison": "ICI vs Rescue",
                     "Pair": name, "CellType": "All_spots", "Module": module, "n1": 2, "n2": 2,
                     "diff": float(r["diff"].iloc[0]), "p": float(r.perm_p.iloc[0]), "source_q": float(r.q.iloc[0])})

res = pd.DataFrame(rows)
res["primary_q_within_dataset"] = np.nan
for (dataset, comparison), idx in res.groupby(["Dataset", "Comparison"]).groups.items():
    res.loc[idx, "primary_q_within_dataset"] = bh(res.loc[idx, "p"].values)
res.to_csv(OUT / "planb_primary_four_pairs_v1.csv", index=False)
print(res.round(4).to_string(index=False))
