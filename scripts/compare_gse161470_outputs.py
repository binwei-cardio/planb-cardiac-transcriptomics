# -*- coding: utf-8 -*-
"""Compare GSE161470 clean-room outputs with the original project outputs."""
from pathlib import Path
import sys
import pandas as pd
if len(sys.argv)!=3:
    raise SystemExit('usage: compare_gse161470_outputs.py <original_root> <repro_root>')
old=Path(sys.argv[1]); new=Path(sys.argv[2]); outdir=new/'05_compare'; outdir.mkdir(parents=True,exist_ok=True)
files=['gse161470_controlscore_cells.csv.gz','gse161470_controlscore_pseudobulk_celltype.csv','gse161470_controlscore_celltype_directional.csv']
rows=[]
for f in files:
    a=pd.read_csv(old/'output'/f); b=pd.read_csv(new/'03_output'/f)
    same_cols=list(a.columns)==list(b.columns); same_shape=a.shape==b.shape
    exact=False; maxdiff=None
    if same_cols and same_shape:
        try:
            exact=a.equals(b)
        except Exception:
            exact=False
        if not exact:
            num=a.select_dtypes('number').columns
            if len(num): maxdiff=float((a[num]-b[num]).abs().max().max())
    rows.append({'file':f,'original_rows':a.shape[0],'clean_rows':b.shape[0],'same_columns':same_cols,'same_shape':same_shape,'exactly_equal':exact,'max_numeric_difference':maxdiff})
report=pd.DataFrame(rows); report.to_csv(outdir/'GSE161470_comparison.csv',index=False)
print(report.to_string(index=False)); print('\nAll exact:',bool(report.exactly_equal.all())); print('wrote',outdir/'GSE161470_comparison.csv')
sys.exit(0 if report.exactly_equal.all() else 1)
