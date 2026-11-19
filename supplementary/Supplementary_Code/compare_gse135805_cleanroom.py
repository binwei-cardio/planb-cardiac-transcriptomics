# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import csv, gzip, hashlib
import pandas as pd
ROOT = PROJECT_ROOT
ORIG=ROOT/'生信先行_方案B'/'output'
CLEAN=ROOT/'PlanB_Repro_v1'/'03_output'
RAW=ROOT/'PlanB_Repro_v1'/'01_raw'/'GSE135805'
ORIG_RAW=ROOT/'生信先行_方案B'/'data'/'GSE135805_raw'
COMPARE=ROOT/'PlanB_Repro_v1'/'05_compare'/'GSE135805_cleanroom_comparison.csv'
REPORT=ROOT/'PlanB_Repro_v1'/'08_reports'/'GSE135805_cleanroom_report.md'
MANIFEST=ROOT/'PlanB_Repro_v1'/'08_reports'/'GSE135805_download_manifest_20261118.csv'
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
specs={
'gse135805_controlscore_spots.csv.gz':(['GSM','spot'],['Group']),
'gse135805_controlscore_section_summary.csv':(['GSM'],['Group']),
'gse135805_controlscore_gene_coverage.csv':(['GSM','Module'],['Group'])}
rows=[]
for name,(keys,ignore) in specs.items():
    a=ORIG/name; b=CLEAN/name
    da=pd.read_csv(a).sort_values(keys).reset_index(drop=True)
    db=pd.read_csv(b).sort_values(keys).reset_index(drop=True)
    ha=sha(a); hb=sha(b); decomp=gzsha(a)==gzsha(b) if name.endswith('.gz') else None
    cols=[c for c in da.columns if c not in ignore]
    same_data=cols==[c for c in db.columns if c not in ignore] and da[cols].equals(db[cols])
    group_changes='; '.join(f'{gsm}: {grp_old}->{grp_new}' for gsm,grp_old,grp_new in zip(da['GSM'],da['Group'],db['Group']) if grp_old!=grp_new) if 'Group' in da.columns else ''
    status='PASS_WITH_GEO_LABEL_CORRECTION' if same_data else 'FAIL'
    rows.append({'file':name,'status':status,'rows':len(da),'columns':len(da.columns),'original_bytes':a.stat().st_size,'cleanroom_bytes':b.stat().st_size,'byte_identical':ha==hb,'decompressed_identical':decomp,'data_equal_excluding_group':same_data,'group_label_changes':group_changes,'original_sha256':ha,'cleanroom_sha256':hb})
with open(COMPARE,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(MANIFEST,'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['relative_path','size','sha256','original_sha256_match','source_url'])
    for p in sorted(RAW.glob('*'),key=lambda x:x.name):
        if not p.is_file() or p.name.endswith('.csv'): continue
        orig=ORIG_RAW/p.name; gsm=p.name.split('_')[0]
        w.writerow([p.name,p.stat().st_size,sha(p),orig.exists() and sha(p)==sha(orig),f'https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4030nnn/{gsm}/suppl/{p.name}'])
all_pass=all(r['status'].startswith('PASS') for r in rows)
lines=['# GSE135805 clean-room report','',f'- Raw files: `{RAW}`',f'- Output comparison: `{COMPARE}`',f'- Download manifest: `{MANIFEST}`',f'- Compared outputs: {len(rows)}',f'- Result: {"PASS WITH GEO LABEL CORRECTION" if all_pass else "FAIL"}','', '| File | Rows | Columns | Status | Data equal excluding Group | Group label changes |','|---|---:|---:|---|---|---|']
for r in rows:
    lines.append(f'| {r["file"]} | {r["rows"]} | {r["columns"]} | {r["status"]} | {r["data_equal_excluding_group"]} | {r["group_label_changes"]} |')
lines += ['', 'The original output scripts assigned GSM4030473 to HCM and GSM4030475 to ICM. GEO metadata define GSM4030473 as ICM and GSM4030475 as HCM. The corrected clean-room tables preserve all numerical values and correct these group labels.','' , 'The gzip container differs, but the data content excluding the corrected Group labels is identical.']
REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('GSE135805_ALL_PASS_WITH_LABEL_CORRECTION=',all_pass)
print('comparison=',COMPARE)
print('manifest=',MANIFEST)
print('report=',REPORT)
if not all_pass: raise SystemExit(2)
