# -*- coding: utf-8 -*-
"""Strict parallel range downloader v2 with lock, range validation and tar check."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys, os, time, tarfile, urllib.request, shutil

if len(sys.argv) not in (4,5):
    raise SystemExit('usage: parallel_range_download_v2.py <url> <output> <threads> [total_size]')
url=sys.argv[1]; out=Path(sys.argv[2]); threads=int(sys.argv[3]); total_hint=int(sys.argv[4]) if len(sys.argv)==5 else None
out.parent.mkdir(parents=True,exist_ok=True)
parts_dir=out.parent/(out.name+'.parts'); parts_dir.mkdir(parents=True,exist_ok=True)
lock=out.parent/(out.name+'.download.lock')
try:
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY); os.write(fd,str(os.getpid()).encode()); os.close(fd)
except FileExistsError:
    raise SystemExit(f'lock exists: {lock}. Another downloader may be running. Remove lock only if you are sure none is running.')
headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'identity'}

def get_total():
    if total_hint: return total_hint
    req=urllib.request.Request(url,method='HEAD',headers=headers)
    with urllib.request.urlopen(req,timeout=60) as r:
        n=r.headers.get('Content-Length')
        if n: return int(n)
    raise RuntimeError('cannot determine total size')

def parse_content_range(cr):
    # bytes start-end/total
    left,total=cr.split('/',1); start_end=left.split(' ',1)[1]
    s,e=start_end.split('-',1); return int(s),int(e),int(total)

def download(i,start,end):
    part=parts_dir/f'part{i:03d}'
    target=end-start+1; attempt=0
    while True:
        current=part.stat().st_size if part.exists() else 0
        if current>=target: return
        req_start=start+current; attempt+=1
        try:
            req=urllib.request.Request(url,headers={**headers,'Range':f'bytes={req_start}-{end}'})
            with urllib.request.urlopen(req,timeout=120) as r:
                if r.status!=206: raise RuntimeError(f'expected 206 got {r.status}')
                cr=r.headers.get('Content-Range')
                if not cr: raise RuntimeError('missing Content-Range')
                rs,re,total=parse_content_range(cr)
                if rs!=req_start or re!=end or total!=(total_size): raise RuntimeError(f'wrong Content-Range {cr}')
                with open(part,'ab') as f:
                    while True:
                        chunk=r.read(1024*1024)
                        if not chunk: break
                        f.write(chunk)
                        print(f'part {i:02d}: {part.stat().st_size}/{target}',flush=True)
            if part.stat().st_size>=target: return
            raise RuntimeError('short read')
        except Exception as e:
            if attempt>=50: raise
            wait=min(5*attempt,60)
            print(f'part {i:02d}: {type(e).__name__}: {e}; retry in {wait}s',flush=True)
            time.sleep(wait)

total_size=get_total(); print('total',total_size,flush=True)
chunk=(total_size+threads-1)//threads
jobs=[]
for i in range(threads):
    start=i*chunk; end=min(total_size-1,start+chunk-1)
    if start<=end: jobs.append((i,start,end))
print('segments',jobs,flush=True)
try:
    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        futs=[ex.submit(download,i,s,e) for i,s,e in jobs]
        for f in as_completed(futs): print('finished',f.result(),flush=True) if False else None
    temp=out.with_name(out.name+'.assembling')
    with open(temp,'wb') as dst:
        for i,s,e in jobs:
            p=parts_dir/f'part{i:03d}'; expected=e-s+1; actual=p.stat().st_size
            if actual!=expected: raise RuntimeError(f'part {i} size {actual} != {expected}')
            with open(p,'rb') as src: shutil.copyfileobj(src,dst,1024*1024)
    if temp.stat().st_size!=total_size: raise RuntimeError('assembled size mismatch')
    os.replace(temp,out)
    print('assembled',out,flush=True)
    n=0
    with tarfile.open(out,'r:') as t:
        for m in t: n+=1
    print('tar members',n,flush=True)
    print('DOWNLOAD COMPLETE',flush=True)
finally:
    try: lock.unlink()
    except FileNotFoundError: pass
