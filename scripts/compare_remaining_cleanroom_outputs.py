# -*- coding: utf-8 -*-
"""Compare the four already-generated clean-room datasets with original outputs."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import csv, gzip, hashlib
import numpy as np
import pandas as pd

ROOT = PROJECT_ROOT
ORIG = ROOT / '生信先行_方案B' / 'output'
CLEAN = ROOT / 'PlanB_Repro_v1' / '03_output'
COMPARE = ROOT / 'PlanB_Repro_v1' / '05_compare'
REPORTS = ROOT / 'PlanB_Repro_v1' / '08_reports'
COMPARE.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

DATASETS = {
    'GSE161470': [
        'gse161470_controlscore_cells.csv.gz',
        'gse161470_controlscore_pseudobulk_celltype.csv',
        'gse161470_controlscore_celltype_directional.csv',
    ],
    'GSE288222': [
        'gse288222_controlscore_cells.csv.gz',
        'gse288222_controlscore_pseudobulk.csv',
        'gse288222_controlscore_control_genes.csv',
        'gse288222_controlscore_celltype_pseudobulk.csv',
        'gse288222_controlscore_celltype_permutation.csv',
        'gse288222_controlscore_sample_permutation.csv',
    ],
    'GSE297745': [
        'gse297745_controlscore_spots.csv.gz',
        'gse297745_controlscore_pseudobulk.csv',
        'gse297745_controlscore_permutation.csv',
        'gse297745_spatial_niche.csv',
    ],
    'GSE299032': [
        'gse299032_controlscore_cells.csv.gz',
        'gse299032_controlscore_pseudobulk.csv',
        'gse299032_controlscore_celltype_pseudobulk.csv',
        'gse299032_controlscore_summary.csv',
        'gse299032_controlscore_directional.csv',
    ],
}

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(4 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def sha256_gzip_content(path):
    h = hashlib.sha256()
    with gzip.open(path, 'rb') as f:
        while True:
            b = f.read(4 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def numeric_max_diff(dfa, dfb):
    common = [c for c in dfa.columns if c in dfb.columns]
    maxdiff = 0.0
    found = False
    for c in common:
        a = pd.to_numeric(dfa[c], errors='coerce')
        b = pd.to_numeric(dfb[c], errors='coerce')
        if a.notna().any() and b.notna().any():
            diff = float(np.nanmax(np.abs(a.to_numpy(dtype=float) - b.to_numpy(dtype=float))))
            if np.isfinite(diff):
                maxdiff = max(maxdiff, diff)
                found = True
    return maxdiff if found else None

rows = []
for dataset, names in DATASETS.items():
    for name in names:
        a = ORIG / name
        b = CLEAN / name
        base = {'dataset': dataset, 'file': name}
        if not a.is_file() or not b.is_file():
            rows.append({**base, 'status': 'MISSING', 'notes': f'original={a.is_file()}; cleanroom={b.is_file()}'})
            continue
        ha = sha256_file(a); hb = sha256_file(b)
        byte_identical = ha == hb
        decompressed_identical = None
        if name.endswith('.gz'):
            decompressed_identical = sha256_gzip_content(a) == sha256_gzip_content(b)
        dfa = pd.read_csv(a)
        dfb = pd.read_csv(b)
        columns_match = list(dfa.columns) == list(dfb.columns)
        shape_match = dfa.shape == dfb.shape
        exact_dataframe_equal = columns_match and shape_match and dfa.equals(dfb)
        content_equivalent = byte_identical or bool(decompressed_identical) or exact_dataframe_equal
        status = 'PASS' if content_equivalent and columns_match and shape_match else 'FAIL'
        notes = []
        if byte_identical:
            notes.append('byte-identical')
        elif name.endswith('.gz') and decompressed_identical:
            notes.append('gzip container differs; decompressed CSV is identical')
        elif exact_dataframe_equal:
            notes.append('dataframe identical after parsing')
        else:
            notes.append('content difference detected')
        rows.append({
            **base,
            'status': status,
            'original_bytes': a.stat().st_size,
            'cleanroom_bytes': b.stat().st_size,
            'rows': dfa.shape[0],
            'columns': dfa.shape[1],
            'columns_match': columns_match,
            'shape_match': shape_match,
            'byte_identical': byte_identical,
            'decompressed_identical': decompressed_identical,
            'dataframe_equal': exact_dataframe_equal,
            'max_numeric_difference': numeric_max_diff(dfa, dfb),
            'original_sha256': ha,
            'cleanroom_sha256': hb,
            'notes': '; '.join(notes),
        })

fields = sorted({k for r in rows for k in r})
combined_csv = COMPARE / 'PlanB_remaining_cleanroom_comparison_20261118.csv'
with open(combined_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(rows)

summary_lines = []
all_pass = True
for dataset in DATASETS:
    sub = [r for r in rows if r['dataset'] == dataset]
    passed = sum(r['status'] == 'PASS' for r in sub)
    total = len(sub)
    dataset_pass = passed == total
    all_pass = all_pass and dataset_pass
    report = REPORTS / f'{dataset}_cleanroom_report.md'
    lines = [
        f'# {dataset} clean-room comparison report', '',
        f'- Clean-room output directory: `{CLEAN}`',
        f'- Original output directory: `{ORIG}`',
        f'- Compared final control-score outputs: {total}',
        f'- PASS: {passed}',
        f'- FAIL/MISSING: {total - passed}',
        f'- Dataset result: {"PASS" if dataset_pass else "FAIL"}', '',
        '| File | Rows | Columns | Status | Identity | Notes |',
        '|---|---:|---:|---|---|---|',
    ]
    for r in sub:
        identity = 'byte-identical' if r.get('byte_identical') else ('decompressed-identical' if r.get('decompressed_identical') else 'dataframe-equal' if r.get('dataframe_equal') else 'different')
        lines.append(f"| {r['file']} | {r.get('rows','')} | {r.get('columns','')} | {r['status']} | {identity} | {r.get('notes','')} |")
    lines += ['', 'All listed outputs are final analysis outputs generated from clean-room inputs; legacy pilot tables are outside this comparison scope.']
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    summary_lines += [f'## {dataset}', '', f'- Files compared: {total}', f'- PASS: {passed}', f'- Result: {"PASS" if dataset_pass else "FAIL"}', '']

combined_report = REPORTS / 'PlanB_remaining_cleanroom_comparison_20261118.md'
combined_lines = [
    '# Plan B remaining clean-room comparisons', '',
    'Date: 2026-11-18', '',
    f'- Combined comparison CSV: `{combined_csv}`',
    f'- Overall result: {"PASS" if all_pass else "FAIL"}', '',
] + summary_lines + [
    '## Scope',
    '',
    'This audit compares the final control-gene scoring outputs for GSE161470, GSE288222, GSE297745 and GSE299032. Older pilot outputs that were superseded by the final control-gene method are not used as primary comparison targets.',
]
combined_report.write_text('\n'.join(combined_lines) + '\n', encoding='utf-8')
print(f'ALL_PASS={all_pass}')
print(f'comparison={combined_csv}')
print(f'report={combined_report}')
for dataset in DATASETS:
    sub = [r for r in rows if r['dataset'] == dataset]
    print(dataset, 'files=', len(sub), 'pass=', sum(r['status'] == 'PASS' for r in sub))
    for r in sub:
        if r['status'] != 'PASS':
            print('  FAIL', r)
if not all_pass:
    raise SystemExit(2)
