from pathlib import Path
import sys
old=Path(sys.argv[1]); new=Path(sys.argv[2]); out=Path(sys.argv[3])
size=min(old.stat().st_size,new.stat().st_size)
ranges=[]; in_run=False; start=0; pos=0; CH=1024*1024
with old.open('rb') as a, new.open('rb') as b:
    while pos<size:
        x=a.read(min(CH,size-pos)); y=b.read(min(CH,size-pos))
        if x!=y:
            for i,(u,v) in enumerate(zip(x,y)):
                if u!=v:
                    p=pos+i
                    if not in_run: start=p; in_run=True
                elif in_run:
                    ranges.append((start,pos+i-1)); in_run=False
        elif in_run:
            ranges.append((start,pos+len(x)-1)); in_run=False
        pos+=len(x)
if in_run: ranges.append((start,size-1))
out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w',encoding='utf-8') as f:
    f.write('start,end,length\n')
    for s,e in ranges: f.write(f'{s},{e},{e-s+1}\n')
print('size',size,'mismatch_ranges',len(ranges),'mismatch_bytes',sum(e-s+1 for s,e in ranges))
print('first20'); [print(s,e,e-s+1) for s,e in ranges[:20]]
print('wrote',out)
