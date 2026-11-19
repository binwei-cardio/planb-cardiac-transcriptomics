# -*- coding: utf-8 -*-
"""Download the 13 GSE298023 samples used by the final Plan B analysis.

Files are downloaded from NCBI sample-level supplementary URLs, resumed with
curl, verified against filelist.txt sizes, and finally compared with the
previous local raw files by SHA-256.
"""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib, os, subprocess, sys, threading, time

ROOT = PROJECT_ROOT
REPRO = ROOT / 'PlanB_Repro_v1'
RAW = REPRO / '01_raw' / 'GSE298023'
FILELIST = REPRO / '01_raw' / 'GSE298023_filelist.txt'
ORIGINAL = ROOT / '生信先行_方案B' / 'data' / 'GSE298023_raw'
LOG = REPRO / '07_logs' / 'GSE298023_download.log'
RAW.mkdir(parents=True, exist_ok=True)
LOG.parent.mkdir(parents=True, exist_ok=True)

GROUPS = {
    'ICM': ['GSM9004761','GSM9004763','GSM9004765','GSM9004769','GSM9004770'],
    'DCM': ['GSM9004766','GSM9004767','GSM9004771','GSM9004772','GSM9004773','GSM9004778'],
    'Donor': ['GSM9004774','GSM9004775'],
}
GSMS = [g for values in GROUPS.values() for g in values]
GSM_SET = set(GSMS)

expected = {}
with open(FILELIST, 'r', encoding='utf-8') as f:
    for line in f:
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 4 or parts[0] != 'File':
            continue
        name = parts[1]
        if name.split('_')[0] in GSM_SET:
            expected[name] = int(parts[3])

missing_from_filelist = sorted({g for g in GSMS if not any(n.startswith(g + '_') for n in expected)})
if missing_from_filelist:
    raise SystemExit(f'GSMs missing from filelist: {missing_from_filelist}')
if len(expected) != 39:
    raise SystemExit(f'expected 39 files, found {len(expected)}')

print(f'files_to_download={len(expected)} total_bytes={sum(expected.values())}', flush=True)

lock = threading.Lock()
def log(message):
    with lock:
        line = f'{time.strftime("%Y-%m-%d %H:%M:%S")} {message}'
        print(line, flush=True)
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(4 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def download_one(index, name, size):
    gsm = name.split('_')[0]
    sample_dir = 'GSM9004nnn' if gsm.startswith('GSM9004') else 'GSM9004nnn'
    url = f'https://ftp.ncbi.nlm.nih.gov/geo/samples/{sample_dir}/{gsm}/suppl/{name}'
    final = RAW / name
    partial = RAW / (name + '.partial')
    if final.exists() and final.stat().st_size == size:
        return name, 'already-complete'
    if final.exists() and final.stat().st_size != size:
        raise RuntimeError(f'final file has wrong size: {final} {final.stat().st_size} != {size}')
    partial.touch(exist_ok=True)
    ip = '130.14.250.10' if index % 2 == 0 else '130.14.250.11'
    attempt = 0
    while True:
        have = partial.stat().st_size
        if have == size:
            os.replace(partial, final)
            return name, 'downloaded'
        if have > size:
            raise RuntimeError(f'partial file too large: {partial} {have} > {size}')
        attempt += 1
        cmd = [
            'curl.exe', '--ssl-no-revoke', '--http1.1',
            '--resolve', f'ftp.ncbi.nlm.nih.gov:443:{ip}',
            '-A', 'Mozilla/5.0', '-H', 'Accept-Encoding: identity',
            '-L', '--fail', '--silent', '--show-error',
            '--max-time', '1800', '--continue-at', '-',
            '--output', str(partial), url,
        ]
        log(f'START {name} attempt={attempt} have={have}/{size} ip={ip}')
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        new_have = partial.stat().st_size if partial.exists() else 0
        err = proc.stderr.decode('utf-8', errors='replace').strip()
        if new_have == size:
            os.replace(partial, final)
            log(f'DONE {name} bytes={new_have}')
            return name, 'downloaded'
        if proc.returncode != 0:
            log(f'RETRY {name} rc={proc.returncode} have={new_have}/{size} err={err[:300]}')
        else:
            log(f'RETRY {name} short rc=0 have={new_have}/{size}')
        if new_have <= have:
            time.sleep(min(60, 3 * attempt))
        if attempt >= 120:
            raise RuntimeError(f'too many attempts for {name}')

results = []
jobs = list(enumerate(sorted(expected.items())))
with ThreadPoolExecutor(max_workers=1) as ex:
    futures = [ex.submit(download_one, idx, name, size) for idx, (name, size) in jobs]
    for fut in as_completed(futures):
        name, status = fut.result()
        results.append((name, status))
        log(f'COMPLETE {name} status={status}')

size_errors = []
hash_errors = []
for name, size in sorted(expected.items()):
    p = RAW / name
    if not p.exists() or p.stat().st_size != size:
        size_errors.append((name, p.stat().st_size if p.exists() else None, size))
        continue
    orig = ORIGINAL / name
    if not orig.exists():
        hash_errors.append((name, 'missing original reference'))
    elif sha256_file(p) != sha256_file(orig):
        hash_errors.append((name, 'SHA256 mismatch'))

manifest = REPRO / '08_reports' / 'GSE298023_download_manifest_20261118.csv'
manifest.parent.mkdir(parents=True, exist_ok=True)
import csv
with open(manifest, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['relative_path','size','sha256','source_url'])
    for name in sorted(expected):
        p = RAW / name
        if p.exists():
            gsm = name.split('_')[0]
            url = f'https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM9004nnn/{gsm}/suppl/{name}'
            w.writerow([name, p.stat().st_size, sha256_file(p), url])

print(f'size_errors={len(size_errors)} hash_errors={len(hash_errors)}', flush=True)
print(f'manifest={manifest}', flush=True)
if size_errors:
    print('SIZE_ERRORS', size_errors, flush=True)
if hash_errors:
    print('HASH_ERRORS', hash_errors, flush=True)
if size_errors or hash_errors:
    raise SystemExit(2)
print('GSE298023_DOWNLOAD_VERIFIED=PASS', flush=True)




