from pathlib import Path
import sys
if len(sys.argv) != 3:
    raise SystemExit('usage: find_binary_diff_ranges.py <candidate> <reference>')
a=Path(sys.argv[1]); b=Path(sys.argv[2])
sa=a.stat().st_size; sb=b.stat().st_size
print(f'candidate={a} size={sa}')
print(f'reference={b} size={sb}')
if sa != sb:
    raise SystemExit('size mismatch')
ranges=[]
with open(a,'rb') as fa, open(b,'rb') as fb:
    base=0
    while True:
        x=fa.read(4*1024*1024); y=fb.read(4*1024*1024)
        if not x: break
        if x != y:
            start=None; last=None
            for i,(u,v) in enumerate(zip(x,y)):
                if u != v:
                    pos=base+i
                    if start is None: start=pos
                    last=pos
                elif start is not None:
                    ranges.append((start,last))
                    start=last=None
            if start is not None: ranges.append((start,last))
        base += len(x)
print(f'diff_ranges={len(ranges)}')
for start,end in ranges[:200]:
    print(f'{start}\t{end}\t{end-start+1}')
if len(ranges)>200: print(f'... {len(ranges)-200} more ranges')
