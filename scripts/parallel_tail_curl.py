# -*- coding: utf-8 -*-
"""Finish one partial HTTP-range segment using resumable parallel curl chunks."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess, sys, time

if len(sys.argv) != 6:
    raise SystemExit('usage: parallel_tail_curl.py <url> <part_path> <part_global_start> <part_target_size> <workers>')

url = sys.argv[1]
part = Path(sys.argv[2])
part_start = int(sys.argv[3])
part_target = int(sys.argv[4])
workers = int(sys.argv[5])
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
workers = max(1, min(workers, remaining))
base = remaining // workers
extra = remaining % workers

jobs = []
next_global = part_start + current
for idx in range(workers):
    n = base + (1 if idx < extra else 0)
    start = next_global
    end = start + n - 1
    temp = part.with_name(f'{part.name}.curl{idx:02d}')
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
    next_report = 0
    # Stagger connection starts to avoid a burst of 503 responses.
    time.sleep(idx * 1.5)
    while True:
        have = temp.stat().st_size if temp.exists() else 0
        if have > expected:
            raise RuntimeError(f'chunk {idx} too large: {have}>{expected}')
        if have == expected:
            return idx, temp, expected
        req_start = start + have
        attempt += 1
        cmd = [
            'curl.exe', '--ssl-no-revoke', '-L', '--fail', '--silent', '--show-error',
            '--max-time', '900', '--range', f'{req_start}-{end}', url,
        ]
        try:
            with open(temp, 'ab') as out:
                proc = subprocess.run(cmd, stdout=out, stderr=subprocess.PIPE)
        except Exception as e:
            proc = None
            err = str(e)
        else:
            err = proc.stderr.decode('utf-8', errors='replace').strip()
        have = temp.stat().st_size if temp.exists() else 0
        mib = have // (5 * 1024 * 1024)
        if mib >= next_report:
            print(f'curl {idx:02d}: {have}/{expected} bytes', flush=True)
            next_report = mib + 1
        if proc is not None and proc.returncode == 0 and have == expected:
            return idx, temp, expected
        if attempt >= 200:
            raise RuntimeError(f'chunk {idx} failed after {attempt} attempts; {have}/{expected}; {err}')
        wait = min(2 + attempt, 30)
        print(f'curl {idx:02d}: retry {attempt} after {have}/{expected}; curl={getattr(proc, "returncode", "launch-error")}; {err}; wait={wait}s', flush=True)
        time.sleep(wait)


results = {}
with ThreadPoolExecutor(max_workers=workers) as ex:
    futures = [ex.submit(fetch, job) for job in jobs]
    for future in as_completed(futures):
        idx, temp, expected = future.result()
        results[idx] = (temp, expected)
        print(f'curl {idx:02d}: COMPLETE', flush=True)

for idx, start, end, temp in jobs:
    expected = end - start + 1
    temp, got = results[idx]
    actual = temp.stat().st_size
    if actual != expected or got != expected:
        raise RuntimeError(f'chunk {idx} verification failed: {actual}/{expected}')

current_now = part.stat().st_size
if current_now != current:
    raise RuntimeError(f'part changed while downloading tail: {current_now} != {current}')

with open(part, 'ab') as dst:
    for idx, start, end, temp in jobs:
        print(f'appending curl chunk {idx:02d}', flush=True)
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
