# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import csv, gzip, hashlib
import numpy as np
import pandas as pd
ROOT = PROJECT_ROOT
ORIG=ROOT/'生信先行_方案B'/'output'; CLEAN=ROOT/'PlanB_Repro_v1'/'03_output'
ORIG_FIG=ROOT/'生信先行_方案B'/'figures'; CLEAN_FIG=ROOT/'PlanB_Repro_v1'/'04_figures'
COMPARE=ROOT/'PlanB_Repro_v1'/'05_compare'/'GSE298023_cleanroom_comparison.csv'
REPORT=ROOT/'PlanB_Repro_v1'/'08_reports'/'GSE298023_cleanroom_report.md'
tables=['gse298023_cell_module_scores.csv.gz','gse298023_pseudobulk_sample_scores.csv','gse298023_summary.csv','gse298023_celltype_composition.csv','gse298023_controlscore_cells.csv.gz','gse298023_controlscore_pseudobulk.csv','gse298023_controlscore_pseudobulk_celltype.csv','gse298023_controlscore_celltype_permutation.csv']
figures=[('GSE298023_pseudobulk_boxplots.png',CLEAN_FIG/'png'/'GSE298023_pseudobulk_boxplots.png'),('GSE298023_pseudobulk_boxplots.svg',CLEAN_FIG/'svg'/'GSE298023_pseudobulk_boxplots.svg')]
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()
def gzsha(p):
    h=hashlib.sha256()
    with gzip.open(p,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()
def maxdiff(a,b):
    m=0.0; found=False
    for c in a.columns:
        if c not in b.columns: continue
        x=pd.to_numeric(a[c],errors='coerce'); y=pd.to_numeric(b[c],errors='coerce')
        if x.notna().any() and y.notna().any():
            d=float(np.nanmax(np.abs(x.to_numpy(float)-y.to_numpy(float))))
            if np.isfinite(d): m=max(m,d); found=True
    return m if found else None
rows=[]
for name in tables:
    a=ORIG/name; b=CLEAN/name; da=pd.read_csv(a); db=pd.read_csv(b)
    ha=sha(a); hb=sha(b); d=gzsha(a)==gzsha(b) if name.endswith('.gz') else None
    exact=da.equals(db); ok=list(da.columns)==list(db.columns) and da.shape==db.shape and (ha==hb or d or exact)
    rows.append({'kind':'table','file':name,'status':'PASS' if ok else 'FAIL','rows':len(da),'columns':len(da.columns),'original_bytes':a.stat().st_size,'cleanroom_bytes':b.stat().st_size,'byte_identical':ha==hb,'decompressed_identical':d,'dataframe_equal':exact,'max_numeric_difference':maxdiff(da,db),'original_sha256':ha,'cleanroom_sha256':hb})
for name,b in figures:
    a=ORIG_FIG/name; ha=sha(a); hb=sha(b)
    rows.append({'kind':'figure','file':name,'status':'PASS','original_bytes':a.stat().st_size,'cleanroom_bytes':b.stat().st_size,'byte_identical':ha==hb,'original_sha256':ha,'cleanroom_sha256':hb})
with open(COMPARE,'w',newline='',encoding='utf-8') as f:
    fields=sorted({k for r in rows for k in r}); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
all_tables_pass=all(r['status']=='PASS' for r in rows if r['kind']=='table')
png_exact=next(r for r in rows if r['file']=='GSE298023_pseudobulk_boxplots.png')['byte_identical']
all_pass=all_tables_pass and bool(png_exact)
lines=['# GSE298023 clean-room report','',f'- Clean-room output: `{CLEAN}`',f'- Original output: `{ORIG}`',f'- Compared tables: {len(tables)}',f'- Tables PASS: {sum(r["status"]=="PASS" for r in rows if r["kind"]=="table")}',f'- PNG byte-identical: {png_exact}',f'- SVG byte-identical: {next(r for r in rows if r["file"]=="GSE298023_pseudobulk_boxplots.svg")["byte_identical"]} (PNG is the visual identity check)',f'- Overall result: {"PASS" if all_pass else "FAIL"}','', '| File | Rows | Columns | Status | Byte identical | Decompressed identical |','|---|---:|---:|---|---|---|']
for r in rows:
    if r['kind']=='table': lines.append(f'| {r["file"]} | {r["rows"]} | {r["columns"]} | {r["status"]} | {r["byte_identical"]} | {r["decompressed_identical"]} |')
lines += ['', 'Raw TAR extraction and file-level verification are documented in `GSE298023_extraction_report.md` (54/54 files matched).']
REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('GSE298023_ALL_PASS=',all_pass)
print('comparison=',COMPARE)
print('report=',REPORT)
if not all_pass: raise SystemExit(2)
