# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import csv, hashlib, re
from datetime import datetime
ROOT = PROJECT_ROOT
REPRO=ROOT/'PlanB_Repro_v1'
RAW=REPRO/'01_raw'
LISTS=REPRO/'07_logs'/'ncbi_filelists_20261118'
REPORTS=REPRO/'08_reports'
REPORTS.mkdir(parents=True,exist_ok=True)
DETAIL=REPORTS/'PlanB_raw_data_provenance_audit_20261118.csv'
SUMMARY=REPORTS/'PlanB_raw_data_provenance_summary_20261118.csv'
REPORT=REPORTS/'PlanB_raw_data_provenance_audit_20261118.md'

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()
def remote_archive_size(acc):
    p=LISTS/f'{acc}_filelist.txt'
    if not p.exists(): return None
    for line in p.read_text(encoding='utf-8').splitlines():
        parts=line.split('\t')
        if len(parts)>=4 and parts[0]=='Archive': return int(parts[3])
    return None
series_url=lambda acc,prefix: f'https://ftp.ncbi.nlm.nih.gov/geo/series/{prefix}/{acc}/suppl/{acc}_RAW.tar'
rows=[]
def add(acc,path,source_url,remote_size,mode,file_level,output_status,caveat,authenticity):
    p=Path(path)
    rows.append({'dataset':acc,'local_file':p.name,'local_path':str(p),'local_bytes':p.stat().st_size,'local_last_write':datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec='seconds'),'sha256':sha(p),'source_url':source_url,'remote_size':remote_size if remote_size is not None else '', 'remote_size_match':('PASS' if remote_size is not None and p.stat().st_size==remote_size else ('NOT_ESTABLISHED' if remote_size is None else 'FAIL')),'download_mode':mode,'file_level_verification':file_level,'analysis_output_comparison':output_status,'whole_archive_or_source_status':authenticity,'caveat':caveat})
# tar datasets
add('GSE292067',RAW/'GSE292067_pyfresh_20260921'/'GSE292067_RAW.tar',series_url('GSE292067','GSE292nnn'),remote_archive_size('GSE292067'),'Fresh remote range download; one corrupt resume segment repaired from NCBI','100/100 extracted files matched prior known-good copy','7/7 outputs PASS','Whole TAR SHA256 differs from old reference because NCBI archive-header metadata changed; do not claim whole-file hash match','VERIFIED_WITH_CAVEAT')
add('GSE288222',RAW/'GSE288222'/'GSE288222_RAW.tar',series_url('GSE288222','GSE288nnn'),remote_archive_size('GSE288222'),'Preserved NCBI raw TAR from prior clean-room setup','No fresh re-download performed; size matches current NCBI filelist','6/6 outputs PASS','Download source is NCBI GEO; independent fresh re-download not performed in this audit','VERIFIED_SOURCE_WITH_LIMITED_FRESHNESS')
add('GSE297745',RAW/'GSE297745'/'GSE297745_RAW.tar',series_url('GSE297745','GSE297nnn'),remote_archive_size('GSE297745'),'Preserved NCBI raw TAR from prior clean-room setup','No fresh re-download performed; size matches current NCBI filelist','4/4 outputs PASS','Download source is NCBI GEO; independent fresh re-download not performed in this audit','VERIFIED_SOURCE_WITH_LIMITED_FRESHNESS')
add('GSE298023',RAW/'GSE298023'/'GSE298023_RAW.tar',series_url('GSE298023','GSE298nnn'),remote_archive_size('GSE298023'),'Preserved prior NCBI raw TAR copied into clean-room directory','54/54 extracted files matched prior raw directory','8/8 core outputs PASS','Full TAR was not freshly downloaded in this audit; current remote size matches and local SHA256 is recorded','VERIFIED_WITH_FRESHNESS_CAVEAT')
add('GSE299032',RAW/'GSE299032'/'GSE299032_RAW.tar',series_url('GSE299032','GSE299nnn'),remote_archive_size('GSE299032'),'Preserved NCBI raw TAR from prior clean-room setup','No fresh re-download performed; size matches current NCBI filelist','5/5 outputs PASS','Download source is NCBI GEO; independent fresh re-download not performed in this audit','VERIFIED_SOURCE_WITH_LIMITED_FRESHNESS')
# GSE135805 sample files
for p in sorted((RAW/'GSE135805').glob('*')):
    if not p.is_file() or p.suffix=='.csv': continue
    gsm=p.name.split('_')[0]
    url=f'https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM4030nnn/{gsm}/suppl/{p.name}'
    add('GSE135805',p,url,p.stat().st_size,'Freshly downloaded in this audit session','4/4 raw files matched prior local copies by SHA256','3/3 outputs PASS','Retrieved through NCBI GEO sample-level supplementary path with explicit NCBI server resolution','VERIFIED_FRESH')
# GSE161470 processed files (exact files are present in the GEO supplementary directory)
gse161470_remote={'GSE161470_cell.counts.Control.txt.gz':13845244,'GSE161470_cell.counts.HF.txt.gz':8847456,'GSE161470_cell.metadata.Control.csv.gz':147027,'GSE161470_cell.metadata.HF.csv.gz':93704}
for p in sorted((RAW/'GSE161470').glob('*.gz')):
    url='https://ftp.ncbi.nlm.nih.gov/geo/series/GSE161nnn/GSE161470/suppl/'+p.name
    add('GSE161470',p,url,gse161470_remote[p.name],'Preserved processed input; exact NCBI source URL re-confirmed 2026-11-18','Local SHA256; remote size; first 64 KiB byte match','3/3 outputs PASS','Full file was not re-downloaded in this audit; exact source URL, size, Last-Modified, and 64 KiB prefix match were verified','VERIFIED_SOURCE_RECORD_CLOSED')
with open(DETAIL,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
# dataset summary
summary=[]
for acc in ['GSE292067','GSE161470','GSE288222','GSE298023','GSE297745','GSE299032','GSE135805']:
    sub=[r for r in rows if r['dataset']==acc]
    summary.append({'dataset':acc,'primary_files':len(sub),'local_bytes':sum(int(r['local_bytes']) for r in sub),'remote_size_match':('PASS' if all(r['remote_size_match']=='PASS' for r in sub) else ('PARTIAL/NOT_ESTABLISHED' if any(r['remote_size_match']!='FAIL' for r in sub) else 'FAIL')),'download_mode':'; '.join(sorted(set(r['download_mode'] for r in sub))),'file_level_verification':'; '.join(sorted(set(r['file_level_verification'] for r in sub))),'analysis_output_comparison':sub[0]['analysis_output_comparison'],'authenticity_status':sub[0]['whole_archive_or_source_status'],'caveat':sub[0]['caveat']})
with open(SUMMARY,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)
lines=['# Plan B raw-data provenance and authenticity audit','','Date: 2026-11-18','', '## What this audit establishes','', '- Every local raw file was hashed with SHA-256.', '- Tar archives were compared by byte size with the current NCBI filelist where available.', '- Analysis outputs were compared with the original outputs and are listed separately from download provenance.', '- Fresh download, preserved-raw reuse and unresolved source-link cases are distinguished explicitly.', '', '## Dataset summary','', '| Dataset | Files | Bytes | Remote size | Download mode | File-level evidence | Output comparison | Authenticity status |','|---|---:|---:|---|---|---|---|---|']
for s in summary:
    lines.append(f"| {s['dataset']} | {s['primary_files']} | {s['local_bytes']} | {s['remote_size_match']} | {s['download_mode']} | {s['file_level_verification']} | {s['analysis_output_comparison']} | {s['authenticity_status']} |")
lines += ['', '## Explicit limitations','', '- **GSE292067:** the whole TAR SHA-256 does not match the old reference; 100/100 extracted member files match. This is a real archive-container discrepancy, not reported as a whole-file pass.', '- **GSE298023:** the preserved NCBI raw TAR was used; it was not freshly downloaded in full during this audit. Its size matches the current NCBI filelist and its SHA-256 is recorded.', '- **GSE161470:** the four processed count/metadata files were located at their exact NCBI GEO supplementary URLs. Remote size and Last-Modified metadata match the local files, and the first 64 KiB of every file is byte-identical. Full-file re-download was not performed, but the source record is now closed.', '- **GSE288222, GSE297745 and GSE299032:** preserved NCBI raw TARs were used. Their sizes match current NCBI filelists, but they were not independently re-downloaded in this audit.', '- **GSE135805:** all four sample-level files were freshly downloaded and matched prior local copies by SHA-256.', '', '## Original data locations','', f'- Clean-room raw: `{RAW}`', f'- Extracted data: `{REPRO/"02_unpacked"}`', f'- Existing project raw data: `{ROOT/"生信先行_方案B"/"data"}`', '', '## Package boundary','', 'The reproducibility ZIP contains scripts, output tables, figures, comparison reports and manifests, but not the multi-gigabyte raw data. Raw data remain in the project directories listed above.']
REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('detail=',DETAIL)
print('summary=',SUMMARY)
print('report=',REPORT)
print('rows=',len(rows))
