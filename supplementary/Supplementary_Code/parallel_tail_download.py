# -*- coding: utf-8 -*-
"""Resume and finish one known part file using parallel HTTP range requests."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys, time, urllib.request
import hashlib

if len(sys.argv) != 7:
    raise SystemExit('usage: parallel_tail_download.py <url> <part_path> <part_global_start> <part_target_size> <workers> <log_prefix>')

url = sys.argv[1]
part = Path(sys.argv[2])
part_start = int(sys.argv[3])
part_target = int(sys.argv[4])
workers = int(sys.argv[5])
log_prefix = sys.argv[6]

headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'identity'}
part_end = part_start + part_target - 1

if not part.exists():
    part.parent.mkdir(parents=True, exist_ok=True)
    part.touch()

current = part.stat().st_size
if current > part_target:
    raise SystemExit(f'part is too large: {current} > {part_target}')
if current == part_target:
    print(f'PART ALREADY COMPLETE: {part}', flush=True)
    raise SystemExit(0)

remaining = part_target - current
# Keep chunks reasonably small so a single slow/timing-out connection does not hold up the tail.
chunk_size = 1024 * 1024
workers = max(1, min(workers, (remaining + chunk_size - 1) // chunk_size))
base = remaining // workers
extra = remaining % workers

jobs = []
next_global = part_start + current
for idx in range(workers):
    n = base + (1 if idx < extra else 0)
    start = next_global
    end = start + n - 1
    temp = part.with_name(f'{part.name}.tail{idx:02d}')
    jobs.append((idx, start, end, temp))
    next_global = end + 1
assert next_global == part_end + 1

print(f'part={part}', flush=True)
print(f'part_start={part_start} target={part_target} current={current} remaining={remaining}', flush=True)
print(f'workers={workers} chunk_bytes~={base}', flush=True)


def fetch(job):
    idx, start, end, temp = job
    expected = end - start + 1
    attempt = 0
    last_report = -1
    while True:
        have = temp.stat().st_size if temp.exists() else 0
        if have > expected:
            raise RuntimeError(f'chunk {idx} too large: {have}>{expected}')
        if have == expected:
            return idx, temp, expected
        req_start = start + have
        attempt += 1
        try:
            req = urllib.request.Request(url, headers={**headers, 'Range': f'bytes={req_start}-{end}'})
            with urllib.request.urlopen(req, timeout=180) as r:
                if r.status != 206:
                    raise RuntimeError(f'expected 206, got {r.status}')
                with open(temp, 'ab') as f:
                    while True:
                        have = temp.stat().st_size
                        if have >= expected:
                            break
                        block = r.read(min(256 * 1024, expected - have))
                        if not block:
                            break
                        f.write(block)
                        f.flush()
                        have = temp.stat().st_size
                        mib = have // (1024 * 1024)
                        if mib != last_report:
                            print(f'tail {idx:02d}: {have}/{expected} bytes', flush=True)
                            last_report = mib
            have = temp.stat().st_size
            if have == expected:
                return idx, temp, expected
            raise RuntimeError(f'short read: {have}/{expected}')
        except Exception as e:
            if attempt >= 80:
                raise
            wait = min(2 * attempt, 30)
            print(f'tail {idx:02d}: error after {have}/{expected}: {e}; retry in {wait}s', flush=True)
            time.sleep(wait)


results = {}
with ThreadPoolExecutor(max_workers=workers) as ex:
    futures = [ex.submit(fetch, job) for job in jobs]
    for future in as_completed(futures):
        idx, temp, expected = future.result()
        results[idx] = (temp, expected)
        print(f'tail {idx:02d}: COMPLETE', flush=True)

for idx, start, end, temp in jobs:
    expected = end - start + 1
    temp, got = results[idx]
    actual = temp.stat().st_size
    if actual != expected or got != expected:
        raise RuntimeError(f'chunk {idx} verification failed: {actual}/{expected}')

# Re-check before touching the source part.
current_now = part.stat().st_size
if current_now != current:
    raise RuntimeError(f'part changed while downloading tail: {current_now} != {current}')

with open(part, 'ab') as dst:
    for idx, start, end, temp in jobs:
        print(f'appending tail {idx:02d}', flush=True)
        with open(temp, 'rb') as src:
            while True:
                block = src.read(1024 * 1024)
                if not block:
                    break
                dst.write(block)
        dst.flush()

final = part.stat().st_size
if final != part_target:
    raise RuntimeError(f'final part size {final} != {part_target}')

for idx, start, end, temp in jobs:
    temp.unlink(missing_ok=True)

print(f'PART COMPLETE size={final}', flush=True)
