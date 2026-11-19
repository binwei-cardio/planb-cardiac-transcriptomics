# -*- coding: utf-8 -*-
from pathlib import Path
import hashlib, sys, tarfile

if len(sys.argv) != 3:
    raise SystemExit('usage: compare_tar_members.py <candidate.tar> <reference.tar>')

def inspect(path):
    out = {}
    errors = []
    with tarfile.open(path, 'r:*') as tf:
        members = tf.getmembers()
        for m in members:
            if not m.isfile():
                continue
            h = hashlib.sha256()
            try:
                f = tf.extractfile(m)
                if f is None:
                    errors.append((m.name, 'extractfile returned None'))
                    continue
                while True:
                    block = f.read(1024 * 1024)
                    if not block:
                        break
                    h.update(block)
                out[m.name] = (m.size, h.hexdigest())
            except Exception as e:
                errors.append((m.name, repr(e)))
    return out, errors

cand, ce = inspect(sys.argv[1])
ref, re = inspect(sys.argv[2])
print(f'candidate_members={len(cand)} candidate_errors={len(ce)}')
print(f'reference_members={len(ref)} reference_errors={len(re)}')
cs=set(cand); rs=set(ref)
print(f'names_only_candidate={len(cs-rs)}')
print(f'names_only_reference={len(rs-cs)}')
mismatches=[]
for name in sorted(cs & rs):
    if cand[name] != ref[name]:
        mismatches.append((name, cand[name], ref[name]))
print(f'content_or_size_mismatches={len(mismatches)}')
for row in mismatches[:50]: print('MISMATCH', row)
for row in ce[:20]: print('CAND_ERROR', row)
for row in re[:20]: print('REF_ERROR', row)
all_ok = not ce and not re and cs == rs and not mismatches
print('FILE_LEVEL_EQUIVALENT=' + ('TRUE' if all_ok else 'FALSE'))
