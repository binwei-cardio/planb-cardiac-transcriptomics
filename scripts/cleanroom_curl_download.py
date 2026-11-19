# -*- coding: utf-8 -*-
"""Clean-room parallel download with strict per-part curl range checks."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess, hashlib, math, json, time

ROOT = PLANB_ROOT
OUTDIR=ROOT/'01_raw'/'GSE292067_curlfresh_20260921'
OUTDIR.mkdir(parents=True,exist_ok=True)
URL='https://ftp.ncbi.nlm.nih.gov/geo/series/GSE292nnn/GSE292067/suppl/GSE292067_RAW.tar'
TOTAL=1634324480
THREADS=6
OUT=OUTDIR/'GSE292067_RAW.tar'
CURL=os.environ.get('CURL_BIN','curl')
CHUNK=math.ceil(TOTAL/THREADS)

jobs=[]
for i in range(THREADS):
    start=i*CHUNK; end=min(TOTAL-1,start+CHUNK-1)
    if start>end: continue
    part=OUT.with_name(OUT.name+f'.part{i:02d}')
    if part.exists(): part.unlink()
    cmd=[CURL,'-L','--ssl-no-revoke','--fail','--retry','10','--retry-delay','5','--retry-all-errors','--range',f'{start}-{end}','-o',str(part),URL]
    log=OUTDIR/f'part{i:02d}.log'
    f=open(log,'wb')
    p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=f)
    jobs.append({'i':i,'start':start,'end':end,'target':end-start+1,'part':part,'proc':p,'log':log,'file':f})

for j in jobs:
    rc=j['proc'].wait(); j['file'].close(); j['returncode']=rc
    actual=j['part'].stat().st_size if j['part'].exists() else 0
    j['actual']=actual
    print(f"part {j['i']:02d}: rc={rc} size={actual}/{j['target']}")

bad=[j for j in jobs if j['returncode']!=0 or j['actual']!=j['target']]
if bad:
    report={'status':'FAILED_PART_SIZE','total':TOTAL,'jobs':[{k:str(v) for k,v in j.items() if k not in ('proc','file')} for j in jobs]}
    (OUTDIR/'download_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    raise SystemExit('part validation failed; see download_report.json')

if OUT.exists(): OUT.unlink()
with open(OUT,'wb') as dst:
    for j in sorted(jobs,key=lambda x:x['i']):
        with open(j['part'],'rb') as src:
            while True:
                b=src.read(8*1024*1024)
                if not b: break
                dst.write(b)
        j['part'].unlink()

size=OUT.stat().st_size
h=hashlib.sha256()
with open(OUT,'rb') as f:
    for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
sha=h.hexdigest().upper()
report={'status':'COMPLETE' if size==TOTAL else 'SIZE_MISMATCH','bytes':size,'target':TOTAL,'sha256':sha}
(OUTDIR/'download_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
if size!=TOTAL: raise SystemExit(1)
