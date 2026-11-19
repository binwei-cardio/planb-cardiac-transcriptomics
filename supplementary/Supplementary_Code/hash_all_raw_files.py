# -*- coding: utf-8 -*-
"""Create a complete SHA-256 inventory for every file under Plan B 01_raw."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_paths import PLANB_ROOT

ROOT = PLANB_ROOT
RAW = ROOT / "01_raw"
SUP = ROOT / "06_Manuscript" / "Supplementary_corrected_v2_20261118"

BUCKETS = {
    "GSE292067": "GSE292067",
    "GSE292067_curlfresh_20260921": "GSE292067",
    "GSE292067_pyfresh_20260921": "GSE292067",
    "GSE161470": "GSE161470",
    "GSE161470_provenance_head_20261118": "GSE161470",
    "GSE161470_provenance_redownload_20261118": "GSE161470",
    "GSE298023_filelist.txt": "GSE298023",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify(path):
    name = path.name.lower()
    suffix = path.suffix.lower()
    if any(token in name for token in [".part", ".partial", ".download", ".lock", ".curl", ".tail", "resume_state", "live_test", "range_test", "connection_"]):
        return "PARTIAL_OR_TRANSFER"
    if suffix in {".tar"}:
        return "ARCHIVE"
    if suffix in {".log"}:
        return "LOG"
    if suffix in {".md", ".txt", ".csv", ".html", ".json"}:
        return "METADATA_OR_LISTING"
    return "OTHER"


rows = []
files = sorted(p for p in RAW.rglob("*") if p.is_file())
for index, path in enumerate(files, 1):
    rel = path.relative_to(RAW).as_posix()
    top = rel.split("/", 1)[0]
    bucket = BUCKETS.get(top, top)
    stat = path.stat()
    print(f"[{index}/{len(files)}] {rel}", flush=True)
    rows.append({
        "dataset_bucket": bucket,
        "relative_path": rel,
        "file_name": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "sha256": sha256(path),
        "last_write_time_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "status_class": classify(path),
    })

out = SUP / "Supplementary_Table_S9_Raw_file_SHA256.csv"
with out.open("w", newline="", encoding="utf-8-sig") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

summary_rows = []
for bucket in sorted({r["dataset_bucket"] for r in rows}):
    block = [r for r in rows if r["dataset_bucket"] == bucket]
    summary_rows.append({
        "dataset_bucket": bucket,
        "files": len(block),
        "bytes": sum(r["size_bytes"] for r in block),
        "archives": sum(r["status_class"] == "ARCHIVE" for r in block),
        "partial_or_transfer": sum(r["status_class"] == "PARTIAL_OR_TRANSFER" for r in block),
        "logs": sum(r["status_class"] == "LOG" for r in block),
        "metadata_or_listing": sum(r["status_class"] == "METADATA_OR_LISTING" for r in block),
        "other": sum(r["status_class"] == "OTHER" for r in block),
    })
summary_out = SUP / "Supplementary_Table_S9_Raw_file_summary.csv"
with summary_out.open("w", newline="", encoding="utf-8-sig") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(summary_rows[0].keys()))
    writer.writeheader()
    writer.writerows(summary_rows)

print("raw_files_hashed", len(rows))
print("total_bytes", sum(r["size_bytes"] for r in rows))
print("output", out)
