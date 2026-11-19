# -*- coding: utf-8 -*-
"""Parallel HTTP range downloader with per-part resume and retries."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys, time, urllib.request, urllib.error, shutil

if len(sys.argv) not in (4,5):
    raise SystemExit('usage: parallel_range_download.py <url> <output> <threads> [total_size]')
url=sys.argv[1]; out=Path(sys.argv[2]); threads=int(sys.argv[3]); total_hint=int(sys.argv[4]) if len(sys.argv)==5 else None
out.parent.mkdir(parents=True,exist_ok=True)
headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'identity'}

def head_total():
    req=urllib.request.Request(url,method='HEAD',headers=headers)
    with urllib.request.urlopen(req,timeout=60) as r:
        n=r.headers.get('Content-Length')
        if n: return int(n)

def get_total():
    if total_hint: return total_hint
    try:
        n=head_total()
        if n: return n
    except Exception:
        pass
    req=urllib.request.Request(url,headers={**headers,'Range':'bytes=0-0'})
    with urllib.request.urlopen(req,timeout=60) as r:
        cr=r.headers.get('Content-Range')
        if cr and '/' in cr: return int(cr.rsplit('/',1)[1])
    raise RuntimeError('cannot determine total size')

def download_part(i,start,end):
    part=out.with_name(out.name+f'.part{i:02d}')
    attempt=0
    while True:
        current=part.stat().st_size if part.exists() else 0
        target=end-start+1
        if current>=target: return i,part
        req_start=start+current
        attempt+=1
        try:
            req=urllib.request.Request(url,headers={**headers,'Range':f'bytes={req_start}-{end}'})
            with urllib.request.urlopen(req,timeout=120) as r:
                if r.status!=206:
                    raise RuntimeError(f'expected HTTP 206, got {r.status}')
                with open(part,'ab') as f:
                    current=part.stat().st_size
                    remaining=target-current
                    while remaining>0:
                        chunk=r.read(min(1024*1024, remaining))
                        if not chunk: break
                        f.write(chunk)
                        remaining-=len(chunk)
                        done=part.stat().st_size
                        print(f'part {i:02d}: {done}/{target} bytes',flush=True)
            if part.stat().st_size>=target: return i,part
            raise RuntimeError('short read')
        except Exception as e:
            if attempt>=20: raise
            wait=min(5*attempt,60)
            print(f'part {i:02d}: error {e}; retry in {wait}s',flush=True)
            time.sleep(wait)

total=get_total(); existing=out.stat().st_size if out.exists() else 0
print(f'total={total} existing={existing} remaining={total-existing}')
if existing>total: raise SystemExit('existing file is larger than remote file')
if existing==total:
    print('already complete'); raise SystemExit(0)
remaining=total-existing; chunk=(remaining+threads-1)//threads
jobs=[]
for i in range(threads):
    start=existing+i*chunk; end=min(total-1,start+chunk-1)
    if start<=end: jobs.append((i,start,end))
print('segments:',[(i,s,e) for i,s,e in jobs],flush=True)
with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
    futs=[ex.submit(download_part,i,s,e) for i,s,e in jobs]
    for f in as_completed(futs): print('finished',f.result()[0],flush=True)
parts=[]
for i,s,e in jobs:
    p=out.with_name(out.name+f'.part{i:02d}'); expected=e-s+1; actual=p.stat().st_size
    if actual!=expected: raise RuntimeError(f'part {i} size {actual} != {expected}')
    parts.append(p)
with open(out,'ab') as dst:
    for p in parts:
        with open(p,'rb') as src: shutil.copyfileobj(src,dst,1024*1024)
final=out.stat().st_size
print(f'final size={final} target={total}')
if final!=total: raise SystemExit('final size mismatch')
for p in parts: p.unlink()
print('DOWNLOAD COMPLETE')
