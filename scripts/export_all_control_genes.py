# -*- coding: utf-8 -*-
"""Export all expression-matched control-gene selections used by Plan B.

The selections reproduce the primary scripts with fixed seed 42, 20 expression
bins and at most 10 control genes per programme gene. Outputs S8 document every
selected control at sample/module level and provide a compact summary.
"""
from pathlib import Path
from collections import defaultdict
import gzip
import re
import sys

import numpy as np
import pandas as pd
import scipy.sparse as sp
import h5py

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_paths import PLANB_ROOT
from planb_ucell_lib import load_mtx_dir
from planb_controlscore_lib import control_module_scores

ROOT = PLANB_ROOT
SUP = ROOT / "06_Manuscript" / "Supplementary_corrected_v2_20261118"
OUT = ROOT / "03_output"
RAW = ROOT / "01_raw"
UNPACKED = ROOT / "02_unpacked"
N_CTRL, N_BINS, SEED = 10, 20, 42

s2 = pd.read_csv(SUP / "Supplementary_Table_S2_Module_genes.csv")
for col in ["Programme", "Human_symbol", "Mouse_symbol_used", "Notes"]:
    s2[col] = s2[col].fillna("NA").astype(str)
HUMAN_MODULES = {
    module: group["Human_symbol"].tolist()
    for module, group in s2.groupby("Programme", sort=False)
}
MOUSE_MODULES = {}
for module, group in s2.groupby("Programme", sort=False):
    genes = []
    for human, mouse in zip(group["Human_symbol"], group["Mouse_symbol_used"]):
        if mouse and mouse.upper() != "NA":
            genes.append(mouse)
        elif module != "Senescence" or human != "CXCL8":
            genes.append(human.lower().capitalize())
    MOUSE_MODULES[module] = genes

records = []
summaries = []


def add_controls(dataset, sample_id, gsm, group, unit, modules, controls,
                 present_genes, identifier_type="Gene_symbol"):
    for module in modules:
        ctrl = list(dict.fromkeys(controls.get(module, [])))
        present = [g for g in modules[module] if str(g).upper() in present_genes]
        summaries.append({
            "Dataset": dataset,
            "SampleID": sample_id,
            "GSM": gsm,
            "Group": group,
            "ScoringUnit": unit,
            "Programme": module,
            "ModuleGenesPresent": len(present),
            "UniqueControlGenes": len(ctrl),
            "SelectionSeed": SEED,
            "ExpressionBins": N_BINS,
            "MaxControlsPerModuleGene": N_CTRL,
            "Status": "SELECTED" if len(present) >= 3 and len(ctrl) >= 3 else "NOT_SCORED_OR_INSUFFICIENT_GENES",
        })
        for rank, gene in enumerate(ctrl, 1):
            records.append({
                "Dataset": dataset,
                "SampleID": sample_id,
                "GSM": gsm,
                "Group": group,
                "ScoringUnit": unit,
                "Programme": module,
                "ControlGeneIndex": rank,
                "ControlGeneID": gene,
                "IdentifierType": identifier_type,
                "SelectionSeed": SEED,
                "ExpressionBins": N_BINS,
                "MaxControlsPerModuleGene": N_CTRL,
            })


def score_and_record(dataset, sample_id, gsm, group, X, syms, modules,
                     unit="sample", identifier_type="Gene_symbol"):
    _, controls = control_module_scores(X, syms, modules, n_ctrl=N_CTRL, n_bins=N_BINS, seed=SEED)
    present = {str(x).upper() for x in syms}
    add_controls(dataset, sample_id, gsm, group, unit, modules, controls, present, identifier_type)


# GSE292067: 25 sample-level matrices.
g292_groups = {
    "Donor": [f"GSM8848{n}" for n in range(306, 314)],
    "DoxCM": [f"GSM8848{n}" for n in range(314, 325)],
    "NICM": [f"GSM8848{n}" for n in range(325, 331)],
}
d292 = UNPACKED / "GSE292067_pyfresh_20261115"
for group, gsms in g292_groups.items():
    for gsm in gsms:
        matches = list(d292.glob(f"{gsm}*_matrix.mtx.gz"))
        if not matches:
            print("missing GSE292067", gsm)
            continue
        base = str(matches[0])[:-len("_matrix.mtx.gz")]
        X, syms, _ = load_mtx_dir(base)
        score_and_record("GSE292067", gsm, gsm, group, X, syms, HUMAN_MODULES)
        print("GSE292067", gsm)

# GSE298023: 13 selected non-scar samples; primary scoring omitted Senescence.
g298_groups = {
    "ICM": ["GSM9004761", "GSM9004763", "GSM9004765", "GSM9004769", "GSM9004770"],
    "DCM": ["GSM9004766", "GSM9004767", "GSM9004771", "GSM9004772", "GSM9004773", "GSM9004778"],
    "Donor": ["GSM9004774", "GSM9004775"],
}
mod298 = {k: v for k, v in HUMAN_MODULES.items() if k != "Senescence"}
d298 = UNPACKED / "GSE298023"
for group, gsms in g298_groups.items():
    for gsm in gsms:
        matches = list(d298.glob(f"{gsm}*_matrix.mtx.gz"))
        if not matches:
            print("missing GSE298023", gsm)
            continue
        base = str(matches[0])[:-len("_matrix.mtx.gz")]
        X, syms, _ = load_mtx_dir(base)
        score_and_record("GSE298023", gsm, gsm, group, X, syms, mod298)
        print("GSE298023", gsm)

# GSE297745: 2-vs-2 Visium; primary scoring omitted Senescence.
d297 = UNPACKED / "GSE297745"
samples297 = {
    "GSM8998316": ("ICI", "WO_66093"),
    "GSM8998317": ("ICI", "WO_66094"),
    "GSM8998318": ("Rescue", "WO_66095"),
    "GSM8998319": ("Rescue", "WO_66096"),
}
mod297 = {k: v for k, v in MOUSE_MODULES.items() if k != "Senescence"}
for gsm, (group, suffix) in samples297.items():
    X, syms, _ = load_mtx_dir(str(d297 / f"{gsm}_{suffix}"))
    score_and_record("GSE297745", gsm, gsm, group, X, syms, mod297, unit="all_spots")
    print("GSE297745", gsm)

# GSE299032: heart scRNA-seq H5 files, cells filtered at >=200 counts before scoring.
def load_h5_filtered(path):
    with h5py.File(path, "r") as fh:
        group = fh["matrix"]
        shape = tuple(int(x) for x in group["shape"][:])
        X = sp.csc_matrix(
            (group["data"][:], group["indices"][:], group["indptr"][:]),
            shape=shape,
        ).T.tocsr()
        genes = np.array([
            x.decode() if isinstance(x, bytes) else str(x)
            for x in group["features"]["name"][:]
        ]).astype(str)
        barcodes = np.array([
            x.decode() if isinstance(x, bytes) else str(x)
            for x in group["barcodes"][:]
        ]).astype(str)
    totals = np.asarray(X.sum(axis=1)).ravel()
    keep = totals >= 200
    return X[keep], genes, barcodes[keep]

d299 = UNPACKED / "GSE299032"
samples299 = {
    "GSM9031122_F127_Heart_filtered_feature_bc_matrix.h5": ("ICI-model", "F127", "GSM9031122"),
    "GSM9031128_F1863_Heart_filtered_feature_bc_matrix.h5": ("ICI-model", "F1863", "GSM9031128"),
    "GSM9031134_F234_Heart_filtered_feature_bc_matrix.h5": ("Control", "F234", "GSM9031134"),
    "GSM9031140_M1702_Heart_filtered_feature_bc_matrix.h5": ("ICI-model", "M1702", "GSM9031140"),
    "GSM9876459_558M_Heart_filtered_feature_bc_matrix.h5": ("ICI-model", "558M", "GSM9876459"),
}
for filename, (group, sample_id, gsm) in samples299.items():
    X, syms, _ = load_h5_filtered(d299 / filename)
    score_and_record("GSE299032", sample_id, gsm, group, X, syms, MOUSE_MODULES)
    print("GSE299032", gsm)

# GSE135805: spatial TSV files; module symbols are mapped to Ensembl IDs first.
d135 = RAW / "GSE135805"
map_df = pd.read_csv(ROOT / "06_scripts" / "resources" / "gene_symbol_to_ensembl.csv")
symbol_to_ens = dict(zip(map_df["symbol"].str.upper(), map_df["ensembl"].str.split(".").str[0]))
samples135 = {
    "GSM4030472_smith2_stdata.tsv.gz": ("Normal", "GSM4030472"),
    "GSM4030473_smith3_stdata.tsv.gz": ("ICM", "GSM4030473"),
    "GSM4030474_smith4_stdata.tsv.gz": ("DCM", "GSM4030474"),
    "GSM4030475_smith5_stdata.tsv.gz": ("HCM", "GSM4030475"),
}
for filename, (group, gsm) in samples135.items():
    frame = pd.read_csv(d135 / filename, sep="\t", index_col=0)
    frame.columns = [str(c).split(".")[0] for c in frame.columns]
    frame = frame.T.groupby(level=0).sum().T
    totals = frame.sum(axis=1)
    frame = frame.loc[totals >= 50]
    module_ids = {}
    for module, symbols in HUMAN_MODULES.items():
        module_ids[module] = [
            symbol_to_ens[s]
            for s in symbols
            if s in symbol_to_ens and symbol_to_ens[s] in frame.columns
        ]
    score_and_record(
        "GSE135805", gsm, gsm, group, sp.csr_matrix(frame.values), list(frame.columns),
        module_ids, unit="section", identifier_type="Ensembl_gene_id",
    )
    print("GSE135805", gsm)

# GSE161470: group-level control selection matching the clean-room script.
def first_pass_counts(path):
    sums = defaultdict(float)
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as fh:
        header = fh.readline().strip().split()
        n_cells = len(header)
        for line in fh:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            gene = parts[0].strip('"').upper()
            vals = np.array(parts[1:], dtype=float)
            if len(vals) == n_cells:
                sums[gene] += float(vals.sum())
    return {gene: value / n_cells for gene, value in sums.items()}


def group_controls(means):
    genes = np.array(sorted(means))
    values = np.array([means[g] for g in genes])
    order = np.argsort(values)
    bins = np.empty(len(genes), dtype=int)
    bins[order] = np.floor(np.linspace(0, N_BINS - 1, len(genes))).astype(int)
    g2i = {g: i for i, g in enumerate(genes)}
    rng = np.random.default_rng(SEED)
    result = {}
    for module, symbols in HUMAN_MODULES.items():
        module_genes = [g for g in symbols if g in g2i]
        module_idx = np.array([g2i[g] for g in module_genes], dtype=int)
        selected = []
        seen = set()
        for idx in module_idx:
            candidates = np.where(
                (bins == bins[idx]) & (~np.isin(np.arange(len(genes)), module_idx))
            )[0]
            candidates = [int(i) for i in candidates if int(i) not in seen]
            if candidates:
                picked = rng.choice(candidates, size=min(N_CTRL, len(candidates)), replace=False)
                selected.extend(int(i) for i in picked)
                seen.update(int(i) for i in picked)
        result[module] = [genes[i] for i in selected]
    return result, set(genes)

for group in ["Control", "HF"]:
    path = RAW / "GSE161470" / f"GSE161470_cell.counts.{group}.txt.gz"
    means = first_pass_counts(path)
    controls, present = group_controls(means)
    add_controls(
        "GSE161470", f"{group}_pseudobulk_group", "NA", group, "group_pseudobulk",
        HUMAN_MODULES, controls, present,
    )
    print("GSE161470", group)

# GSE288222: use the already exported primary control table and attach sample metadata.
existing = pd.read_csv(OUT / "gse288222_controlscore_control_genes.csv")
meta = pd.read_csv(OUT / "gse288222_controlscore_pseudobulk.csv")
meta_map = meta.set_index("GSM")[["sample", "Group"]].to_dict("index")
for module, block in existing.groupby("Module", sort=False):
    for gsm, gblock in block.groupby("GSM", sort=False):
        info = meta_map.get(gsm, {"sample": gsm, "Group": "NA"})
        summaries.append({
            "Dataset": "GSE288222",
            "SampleID": info["sample"],
            "GSM": gsm,
            "Group": info["Group"],
            "ScoringUnit": "sample",
            "Programme": module,
            "ModuleGenesPresent": np.nan,
            "UniqueControlGenes": len(gblock),
            "SelectionSeed": SEED,
            "ExpressionBins": N_BINS,
            "MaxControlsPerModuleGene": N_CTRL,
            "Status": "SELECTED" if len(gblock) >= 3 else "NOT_SCORED_OR_INSUFFICIENT_GENES",
        })
        for rank, gene in enumerate(gblock["ControlGene"].tolist(), 1):
            records.append({
                "Dataset": "GSE288222",
                "SampleID": info["sample"],
                "GSM": gsm,
                "Group": info["Group"],
                "ScoringUnit": "sample",
                "Programme": module,
                "ControlGeneIndex": rank,
                "ControlGeneID": gene,
                "IdentifierType": "Gene_symbol",
                "SelectionSeed": SEED,
                "ExpressionBins": N_BINS,
                "MaxControlsPerModuleGene": N_CTRL,
            })
print("GSE288222 existing table")

details = pd.DataFrame(records)
summary = pd.DataFrame(summaries)
details.to_csv(SUP / "Supplementary_Table_S8_Control_gene_selections.csv", index=False, encoding="utf-8-sig")
summary.to_csv(SUP / "Supplementary_Table_S8_Control_gene_summary.csv", index=False, encoding="utf-8-sig")
print("details_rows", len(details))
print("summary_rows", len(summary))
print(summary.groupby("Dataset").agg(Samples=("SampleID", "nunique"), Programmes=("Programme", "nunique"), Controls=("UniqueControlGenes", "sum")).to_string())
