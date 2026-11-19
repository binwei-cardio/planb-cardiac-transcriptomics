# -*- coding: utf-8 -*-
"""Extract GSE292067 fresh TAR and compare every file by SHA-256."""
from pathlib import Path, PurePosixPath
import csv, hashlib, os, sys, tarfile, time

if len(sys.argv) != 6:
    raise SystemExit('usage: extract_verify_gse292067.py <tar> <dest> <reference_dir> <manifest_csv> <comparison_csv>')
tar_path = Path(sys.argv[1])
dest = Path(sys.argv[2])
reference_dir = Path(sys.argv[3])
manifest_path = Path(sys.argv[4])
comparison_path = Path(sys.argv[5])
report_path = manifest_path.with_name('GSE298023_extraction_report.md')
started = time.time()

if not tar_path.is_file():
    raise SystemExit(f'missing TAR: {tar_path}')
if not reference_dir.is_dir():
    raise SystemExit(f'missing reference directory: {reference_dir}')
if dest.exists() and any(dest.iterdir()):
    raise SystemExit(f'destination already exists and is non-empty: {dest}')
dest.mkdir(parents=True, exist_ok=True)
manifest_path.parent.mkdir(parents=True, exist_ok=True)
comparison_path.parent.mkdir(parents=True, exist_ok=True)

def safe_parts(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts:
        raise RuntimeError(f'unsafe TAR member path: {name!r}')
    parts = [x for x in p.parts if x not in ('', '.')]
    if not parts:
        raise RuntimeError(f'empty TAR member path: {name!r}')
    return parts

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            block = f.read(4 * 1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()

manifest = []
with tarfile.open(tar_path, 'r:*') as tf:
    members = tf.getmembers()
    for m in members:
        parts = safe_parts(m.name)
        out = dest.joinpath(*parts)
        if m.isdir():
            out.mkdir(parents=True, exist_ok=True)
            continue
        if not m.isfile():
            raise RuntimeError(f'unsupported non-regular member: {m.name!r} type={m.type!r}')
        out.parent.mkdir(parents=True, exist_ok=True)
        src = tf.extractfile(m)
        if src is None:
            raise RuntimeError(f'cannot read member: {m.name}')
        tmp = out.with_name(out.name + '.partial')
        h = hashlib.sha256()
        size = 0
        with open(tmp, 'wb') as dst:
            while True:
                block = src.read(4 * 1024 * 1024)
                if not block:
                    break
                dst.write(block)
                h.update(block)
                size += len(block)
        if size != m.size:
            raise RuntimeError(f'extracted size mismatch for {m.name}: {size} != {m.size}')
        os.replace(tmp, out)
        try:
            os.utime(out, (m.mtime, m.mtime))
        except Exception:
            pass
        manifest.append({'relative_path': '/'.join(parts), 'size': size, 'sha256': h.hexdigest()})

manifest.sort(key=lambda r: r['relative_path'])
extracted_files = [p for p in dest.rglob('*') if p.is_file()]
if len(extracted_files) != len(manifest):
    raise RuntimeError(f'file count mismatch after extraction: {len(extracted_files)} != {len(manifest)}')

with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['relative_path', 'size', 'sha256'])
    w.writeheader(); w.writerows(manifest)

reference = []
for p in reference_dir.rglob('*'):
    if p.is_file():
        rel = p.relative_to(reference_dir).as_posix()
        reference.append({'relative_path': rel, 'size': p.stat().st_size, 'sha256': sha256_file(p)})
reference.sort(key=lambda r: r['relative_path'])

cmap = {r['relative_path']: r for r in manifest}
rmap = {r['relative_path']: r for r in reference}
all_names = sorted(set(cmap) | set(rmap))
comparison = []
for name in all_names:
    c = cmap.get(name); r = rmap.get(name)
    if c is None:
        status = 'missing_in_extracted'
    elif r is None:
        status = 'missing_in_reference'
    elif c['size'] != r['size']:
        status = 'size_mismatch'
    elif c['sha256'] != r['sha256']:
        status = 'sha256_mismatch'
    else:
        status = 'match'
    comparison.append({
        'relative_path': name,
        'extracted_size': c['size'] if c else '',
        'reference_size': r['size'] if r else '',
        'extracted_sha256': c['sha256'] if c else '',
        'reference_sha256': r['sha256'] if r else '',
        'status': status,
    })

with open(comparison_path, 'w', newline='', encoding='utf-8') as f:
    fields = ['relative_path','extracted_size','reference_size','extracted_sha256','reference_sha256','status']
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(comparison)

match_count = sum(x['status'] == 'match' for x in comparison)
mismatch_count = len(comparison) - match_count
all_match = (len(cmap) == len(rmap) and mismatch_count == 0)
elapsed = round(time.time() - started, 2)
report = [
    '# GSE298023 TAR extraction and file-level verification',
    '',
    f'- TAR: `{tar_path}`',
    f'- TAR size: {tar_path.stat().st_size} bytes',
    f'- Extracted directory: `{dest}`',
    f'- Reference directory: `{reference_dir}`',
    f'- Extracted files: {len(cmap)}',
    f'- Reference files: {len(rmap)}',
    f'- Matching files: {match_count}',
    f'- Mismatches or missing files: {mismatch_count}',
    f'- File-level verification: {"PASS" if all_match else "FAIL"}',
    f'- Elapsed seconds: {elapsed}',
    f'- Manifest: `{manifest_path}`',
    f'- Comparison table: `{comparison_path}`',
    '',
    'Archive-level SHA-256 is recorded separately. Per REPRO_RULES.md, an archive-level hash difference is acceptable only when every extracted data file matches the reference.',
]
report_path.write_text('\n'.join(report) + '\n', encoding='utf-8')
print(f'extracted_files={len(cmap)} reference_files={len(rmap)} matches={match_count} mismatches={mismatch_count}')
print('FILE_LEVEL_VERIFICATION=' + ('PASS' if all_match else 'FAIL'))
print(f'manifest={manifest_path}')
print(f'comparison={comparison_path}')
print(f'report={report_path}')
if not all_match:
    for row in comparison:
        if row['status'] != 'match':
            print('MISMATCH', row)
    raise SystemExit(2)

