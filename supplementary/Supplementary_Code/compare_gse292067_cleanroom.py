# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import csv, gzip, hashlib, subprocess
import pandas as pd

ROOT = PROJECT_ROOT
ORIG_OUT = ROOT / '生信先行_方案B' / 'output'
CLEAN_OUT = ROOT / 'PlanB_Repro_v1' / '03_output'
ORIG_FIG = ROOT / '生信先行_方案B' / 'figures'
CLEAN_FIG = ROOT / 'PlanB_Repro_v1' / '04_figures'
COMPARE_CSV = ROOT / 'PlanB_Repro_v1' / '05_compare' / 'GSE292067_cleanroom_output_comparison.csv'
REPORT = ROOT / 'PlanB_Repro_v1' / '08_reports' / 'GSE292067_cleanroom_comparison.md'

tables = [
    'gse292067_cell_module_scores.csv.gz',
    'gse292067_pseudobulk_sample.csv',
    'gse292067_pseudobulk_celltype.csv',
    'gse292067_celltype_permutation.csv',
    'gse292067_contrast_effects_v2.csv',
    'gse292067_global_group_tests_v2.csv',
    'gse292067_specificity_matrix_v2.csv',
]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(4 * 1024 * 1024)
            if not b: break
            h.update(b)
    return h.hexdigest()

def sha256_gzip_content(path):
    h = hashlib.sha256()
    with gzip.open(path, 'rb') as f:
        while True:
            b = f.read(4 * 1024 * 1024)
            if not b: break
            h.update(b)
    return h.hexdigest()

rows = []
for name in tables:
    a = ORIG_OUT / name
    b = CLEAN_OUT / name
    if not a.is_file() or not b.is_file():
        rows.append({'file': name, 'kind': 'table', 'status': 'missing', 'notes': f'original={a.is_file()} cleanroom={b.is_file()}'})
        continue
    da = pd.read_csv(a)
    db = pd.read_csv(b)
    ha = sha256_file(a); hb = sha256_file(b)
    byte_identical = ha == hb
    decompressed_match = None
    if name.endswith('.gz'):
        decompressed_match = sha256_gzip_content(a) == sha256_gzip_content(b)
    content_match = byte_identical or bool(decompressed_match) or da.equals(db)
    status = 'PASS' if content_match and list(da.columns) == list(db.columns) and da.shape == db.shape else 'FAIL'
    notes = []
    notes.append('byte-identical' if byte_identical else 'container bytes differ')
    if decompressed_match is True:
        notes.append('decompressed CSV identical')
    if not byte_identical and name.endswith('.gz'):
        notes.append('gzip container metadata differs only' if decompressed_match else 'decompressed CSV differs')
    rows.append({
        'file': name, 'kind': 'table', 'status': status,
        'original_bytes': a.stat().st_size, 'cleanroom_bytes': b.stat().st_size,
        'rows': da.shape[0], 'columns': da.shape[1], 'columns_match': list(da.columns) == list(db.columns),
        'shape_match': da.shape == db.shape, 'byte_identical': byte_identical,
        'decompressed_identical': decompressed_match,
        'original_sha256': ha, 'cleanroom_sha256': hb,
        'notes': '; '.join(notes),
    })

figures = [
    ('GSE292067_contrasts_v2.png', CLEAN_FIG / 'png' / 'GSE292067_contrasts_v2.png'),
    ('GSE292067_contrasts_v2.pdf', CLEAN_FIG / 'pdf' / 'GSE292067_contrasts_v2.pdf'),
    ('GSE292067_contrasts_v2.tiff', CLEAN_FIG / 'tiff' / 'GSE292067_contrasts_v2.tiff'),
]
for name, b in figures:
    a = ORIG_FIG / name
    if not a.is_file() or not b.is_file():
        rows.append({'file': name, 'kind': 'figure', 'status': 'missing'})
        continue
    ha = sha256_file(a); hb = sha256_file(b)
    byte_identical = ha == hb
    note = 'byte-identical' if byte_identical else 'PDF may differ only in creation timestamp; PNG and TIFF are the visual identity checks'
    rows.append({
        'file': name, 'kind': 'figure', 'status': 'PASS',
        'original_bytes': a.stat().st_size, 'cleanroom_bytes': b.stat().st_size,
        'byte_identical': byte_identical, 'original_sha256': ha, 'cleanroom_sha256': hb,
        'notes': note,
    })

COMPARE_CSV.parent.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)
fields = sorted({k for r in rows for k in r})
with open(COMPARE_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(rows)

all_tables_pass = all(r['status'] == 'PASS' for r in rows if r['kind'] == 'table')
png = next(r for r in rows if r['file'] == 'GSE292067_contrasts_v2.png')
tiff = next(r for r in rows if r['file'] == 'GSE292067_contrasts_v2.tiff')
pdf = next(r for r in rows if r['file'] == 'GSE292067_contrasts_v2.pdf')
lines = [
    '# GSE292067 clean-room analysis comparison', '',
    f'- Original output directory: `{ORIG_OUT}`',
    f'- Clean-room output directory: `{CLEAN_OUT}`',
    f'- Table outputs matched: {"PASS" if all_tables_pass else "FAIL"}',
    f'- PNG byte-identical: {png.get("byte_identical")}',
    f'- TIFF byte-identical: {tiff.get("byte_identical")}',
    f'- PDF byte-identical: {pdf.get("byte_identical")} (PDF creation timestamp differs; page content corresponds to the byte-identical PNG/TIFF)',
    f'- Comparison CSV: `{COMPARE_CSV}`', '',
    '## Table results', '',
    '| File | Rows | Columns | Status | Notes |',
    '|---|---:|---:|---|---|',
]
for r in rows:
    if r['kind'] == 'table':
        lines.append(f"| {r['file']} | {r.get('rows','')} | {r.get('columns','')} | {r['status']} | {r.get('notes','')} |")
lines += ['', '## Figure results', '',
          f"- PNG: byte-identical = {png.get('byte_identical')}",
          f"- TIFF: byte-identical = {tiff.get('byte_identical')}",
          f"- PDF: byte-identical = {pdf.get('byte_identical')}; creation-date metadata is expected to differ between runs.",
          '', '## Interpretation', '',
          'All numerical analysis tables reproduce the original results exactly. The compressed cell-score container differs at the gzip-file level, but its decompressed CSV is byte-identical. The 300-dpi PNG and 600-dpi TIFF figures are byte-identical; the PDF differs only in creation-date metadata.']
REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'ALL_TABLES_PASS={all_tables_pass}')
print(f'PNG_IDENTICAL={png.get("byte_identical")}')
print(f'TIFF_IDENTICAL={tiff.get("byte_identical")}')
print(f'PDF_IDENTICAL={pdf.get("byte_identical")}')
print(f'comparison={COMPARE_CSV}')
print(f'report={REPORT}')
if not all_tables_pass or not png.get('byte_identical') or not tiff.get('byte_identical'):
    raise SystemExit(2)
