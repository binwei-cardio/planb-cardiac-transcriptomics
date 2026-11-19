# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import csv, hashlib, platform, shutil, sys, zipfile
import numpy, pandas, scipy, matplotlib, PIL
ROOT = PLANB_ROOT
STAGE=ROOT/'PlanB_Reproducibility_Package_v1'
ZIP=ROOT/'PlanB_Reproducibility_Package_v1_20261118.zip'
if STAGE.exists():
    raise SystemExit(f'staging directory already exists: {STAGE}')
if ZIP.exists():
    raise SystemExit(f'zip already exists: {ZIP}')
STAGE.mkdir(parents=True)
copy_map={
    '01_Scripts':ROOT/'06_scripts',
    '02_Reports':ROOT/'08_reports',
    '03_Comparison':ROOT/'05_compare',
    '04_Outputs':ROOT/'03_output',
    '05_Figures':ROOT/'04_figures',
}
for dest_name,src in copy_map.items():
    dest=STAGE/dest_name
    if src.is_dir():
        shutil.copytree(src,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copy2(ROOT/'REPRO_RULES.md',STAGE/'REPRO_RULES.md')
env=STAGE/'06_Environment'
env.mkdir()
versions=[f'python={platform.python_version()}',f'numpy={numpy.__version__}',f'pandas={pandas.__version__}',f'scipy={scipy.__version__}',f'matplotlib={matplotlib.__version__}',f'Pillow={PIL.__version__}',f'platform={platform.platform()}']
(env/'environment_versions.txt').write_text('\n'.join(versions)+'\n',encoding='utf-8')
readme='''# Plan B reproducibility package v1

Date: 2026-11-18

This package contains clean-room scripts, final analysis tables, comparison tables, reports, final figures and figure-QA artifacts for the Plan B cross-dataset study.

Raw public datasets are not bundled because of size. Their accessions, source URLs and SHA-256 manifests are included in `02_Reports`.

Core closure:
- 7/7 datasets completed
- Dataset-level output comparisons passed
- Cross-dataset synthesis outputs reproduced byte-for-byte
- 5/5 final figures passed rendered collision audit and panel-alignment gate

Start with:
- `02_Reports/PlanB_overall_reproduction_report_20261118.md`
- `02_Reports/PlanB_figures_cleanroom_QA_20261118.md`
- `01_Scripts/`
- `03_Comparison/`

`MANIFEST_SHA256.csv` lists every file in this package.
'''
(STAGE/'README.md').write_text(readme,encoding='utf-8')
manifest=STAGE/'MANIFEST_SHA256.csv'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()
rows=[]
for p in sorted(STAGE.rglob('*')):
    if p.is_file() and p!=manifest:
        rows.append({'relative_path':p.relative_to(STAGE).as_posix(),'size':p.stat().st_size,'sha256':sha(p)})
with open(manifest,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['relative_path','size','sha256']); w.writeheader(); w.writerows(rows)
shutil.make_archive(str(ZIP.with_suffix('')),'zip',root_dir=ROOT,base_dir=STAGE.name)
print('stage=',STAGE)
print('zip=',ZIP)
print('zip_bytes=',ZIP.stat().st_size)
print('manifest_files=',len(rows))
