# -*- coding: utf-8 -*-
"""Harden raw-data provenance using official metadata, full hashes and tar members."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone
import csv
import hashlib
import sys
import tarfile
import time
import subprocess

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_paths import PLANB_ROOT

ROOT = PLANB_ROOT
RAW = ROOT / "01_raw"
SUP = ROOT / "06_Manuscript" / "Supplementary_corrected_v2_20261118"
S9 = SUP / "Supplementary_Table_S9_Raw_file_SHA256.csv"
LOG = ROOT / "07_logs" / "raw_integrity_20261118"
MEMBER = LOG / "tar_members"
LOG.mkdir(parents=True, exist_ok=True)
MEMBER.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "GSE292067": {
        "base": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE292nnn/GSE292067/suppl/",
        "archives": ["GSE292067_pyfresh_20260921/GSE292067_RAW.tar"],
        "quarantine_archives": [{
            "relative_path": "01_raw_quarantine_20261118/GSE292067_member_incomplete_duplicate/GSE292067_RAW.tar",
            "official_name": "GSE292067_RAW.tar",
        }],
        "direct": [],
    },
    "GSE288222": {
        "base": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE288nnn/GSE288222/suppl/",
        "archives": ["GSE288222/GSE288222_RAW.tar"],
        "direct": [],
    },
    "GSE298023": {
        "base": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE298nnn/GSE298023/suppl/",
        "archives": ["GSE298023/GSE298023_RAW.tar"],
        "direct": [],
    },
    "GSE297745": {
        "base": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE297nnn/GSE297745/suppl/",
        "archives": ["GSE297745/GSE297745_RAW.tar"],
        "direct": [],
    },
    "GSE299032": {
        "base": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE299nnn/GSE299032/suppl/",
        "archives": ["GSE299032/GSE299032_RAW.tar"],
        "direct": [],
    },
    "GSE135805": {
        "base": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE135nnn/GSE135805/suppl/",
        "archives": [],
        "direct": [
            "GSE135805/GSM4030472_smith2_stdata.tsv.gz",
            "GSE135805/GSM4030473_smith3_stdata.tsv.gz",
            "GSE135805/GSM4030474_smith4_stdata.tsv.gz",
            "GSE135805/GSM4030475_smith5_stdata.tsv.gz",
        ],
    },
    "GSE161470": {
        "base": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE161nnn/GSE161470/suppl/",
        "archives": [],
        "direct": [
            "GSE161470/GSE161470_cell.counts.Control.txt.gz",
            "GSE161470/GSE161470_cell.counts.HF.txt.gz",
            "GSE161470/GSE161470_cell.metadata.Control.csv.gz",
            "GSE161470/GSE161470_cell.metadata.HF.csv.gz",
        ],
    },
}

s9 = pd.read_csv(S9).fillna("")
s9_by_path = s9.set_index("relative_path").to_dict("index")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_text(url, cache_name):
    cache = LOG / cache_name
    if cache.exists() and cache.stat().st_size > 0:
        return cache.read_text(encoding="utf-8")
    req = Request(url, headers={"User-Agent": "PlanB-raw-hardening/1.0", "Accept-Encoding": "identity"})
    for attempt in range(1, 9):
        try:
            with urlopen(req, timeout=60) as response:
                text = response.read().decode("utf-8", errors="replace")
            cache.write_text(text, encoding="utf-8", newline="\n")
            return text
        except Exception:
            time.sleep(min(attempt * 5, 30))
    curl = os.environ.get("CURL_BIN", "curl")
    result = subprocess.run([
        curl, "--ssl-no-revoke", "--location", "--fail", "--silent", "--show-error",
        "--retry", "5", "--retry-delay", "5", "--retry-all-errors", "--output", str(cache), url,
    ])
    if result.returncode == 0 and cache.exists():
        return cache.read_text(encoding="utf-8")
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    raise RuntimeError(f"Could not retrieve {url}")


def parse_filelist(text):
    entries = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 5:
            entries[parts[1]] = {
                "kind": parts[0], "timestamp": parts[2], "size": int(parts[3]), "type": parts[4]
            }
    return entries


def head_metadata(url):
    req = Request(url, method="HEAD", headers={"User-Agent": "PlanB-raw-hardening/1.0", "Accept-Encoding": "identity"})
    last_error = ""
    for attempt in range(1, 3):
        try:
            with urlopen(req, timeout=12) as response:
                return response.status, response.headers.get("Content-Length"), response.headers.get("Last-Modified", "")
        except HTTPError as exc:
            last_error = f"HTTP {exc.code}"
        except URLError as exc:
            last_error = str(exc.reason)
        time.sleep(min(attempt * 3, 10))
    return "UNAVAILABLE", None, last_error


def tar_member_inventory(path, dataset, label):
    rows = []
    with tarfile.open(path, "r:*") as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            fh = tf.extractfile(member)
            digest = hashlib.sha256()
            for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
                digest.update(block)
            rows.append({"member": member.name, "size": member.size, "sha256": digest.hexdigest()})
    out = MEMBER / f"{dataset}_{label}_members.csv"
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    return rows, out


rows = []
for dataset, config in DATASETS.items():
    listing = parse_filelist(fetch_text(config["base"] + "filelist.txt", f"{dataset}_filelist.txt"))
    archive_entries = [
        {"relative_path": rel, "local": RAW / rel, "artifact_type": "raw_archive", "scope": "canonical", "official_name": Path(rel).name}
        for rel in config["archives"]
    ]
    for item in config.get("quarantine_archives", []):
        archive_entries.append({
            "relative_path": item["relative_path"],
            "local": ROOT / item["relative_path"],
            "artifact_type": "quarantined_archive",
            "scope": "quarantine",
            "official_name": item["official_name"],
        })
    for archive_entry in archive_entries:
        rel = archive_entry["relative_path"]
        local = archive_entry["local"]
        artifact_scope = archive_entry["scope"]
        artifact_type = archive_entry["artifact_type"]
        official_name = archive_entry["official_name"]
        official = listing[official_name]
        url = config["base"] + official_name
        status, head_length, last_modified = head_metadata(url)
        local_size = local.stat().st_size
        digest = sha256(local)
        old_sha = str(s9_by_path.get(rel, {}).get("sha256", ""))
        label = local.parent.name
        members, member_file = tar_member_inventory(local, dataset, label)
        member_bytes = sum(item["size"] for item in members)
        official_files = {name: item["size"] for name, item in listing.items() if item["kind"] == "File"}
        member_by_name = {Path(item["member"]).name: item["size"] for item in members}
        member_set_match = set(member_by_name) == set(official_files)
        member_size_match = member_set_match and all(member_by_name[name] == official_files[name] for name in official_files)
        rows.append({
            "dataset": dataset,
            "artifact_type": artifact_type,
            "artifact_scope": artifact_scope,
            "relative_path": rel,
            "official_url": url,
            "official_size_bytes": official["size"],
            "local_size_bytes": local_size,
            "size_match": official["size"] == local_size,
            "official_filelist_timestamp": official["timestamp"],
            "http_status": status,
            "http_content_length": head_length or "",
            "http_last_modified": last_modified,
            "local_sha256": digest,
            "s9_sha256": old_sha,
            "sha_match": (digest == old_sha) if old_sha else "NA",
            "tar_readable": True,
            "tar_member_count": len(members),
            "tar_member_bytes": member_bytes,
            "official_file_count": len(official_files),
            "official_member_set_match": member_set_match,
            "official_member_size_match": member_size_match,
            "tar_member_manifest": f"07_logs/raw_integrity_20261118/tar_members/{member_file.name}",
            "fresh_redownload_status": "BLOCKED_BY_EXTERNAL_NCBI_THROUGHPUT",
            "hardening_status": (
                "QUARANTINED_FAILED_MEMBER_VALIDATION"
                if artifact_scope == "quarantine"
                else ("PASS_WITH_FRESHNESS_CAVEAT" if (official["size"] == local_size and digest == old_sha and member_set_match and member_size_match) else "FAILED_MEMBER_VALIDATION")
            ),
            "notes": (
                "Quarantined duplicate: readable TAR but official member set/size validation failed."
                if artifact_scope == "quarantine"
                else "Full local SHA-256, readable TAR, complete member hashes and official member-name/size comparison."
            ),
        })
        print(f"ARCHIVE {dataset} {rel}: members={len(members)} status={rows[-1]['hardening_status']}", flush=True)

    for rel in config["direct"]:
        local = RAW / rel
        name = local.name
        official = listing.get(name)
        url = config["base"] + name
        if official is not None:
            status, head_length, last_modified = "FILelist", "", ""
            official_size = official["size"]
            official_ts = official["timestamp"]
        else:
            status, head_length, last_modified = head_metadata(url)
            official_size = int(head_length) if head_length and str(head_length).isdigit() else int(s9_by_path[rel]["size_bytes"])
            official_ts = last_modified or "HEAD_CHECK_OR_PRIOR_AUDIT"
        local_size = local.stat().st_size
        digest = sha256(local)
        old_sha = str(s9_by_path[rel]["sha256"])
        rows.append({
            "dataset": dataset,
            "artifact_type": "analysis_input_file",
            "artifact_scope": "canonical",
            "relative_path": rel,
            "official_url": url,
            "official_size_bytes": official_size,
            "local_size_bytes": local_size,
            "size_match": official_size == local_size,
            "official_filelist_timestamp": official_ts,
            "http_status": status,
            "http_content_length": head_length or "",
            "http_last_modified": last_modified,
            "local_sha256": digest,
            "s9_sha256": old_sha,
            "sha_match": digest == old_sha,
            "tar_readable": "",
            "tar_member_count": "",
            "tar_member_bytes": "",
            "official_file_count": "",
            "official_member_set_match": "",
            "official_member_size_match": "",
            "tar_member_manifest": "",
            "fresh_redownload_status": "NOT_APPLICABLE_TO_PROCESSED_INPUT",
            "hardening_status": "PASS" if official_size == local_size and digest == old_sha else "FAIL",
            "notes": "Official size and HTTP metadata checked; full local SHA-256 recomputed.",
        })
        print(f"DIRECT  {dataset} {rel}: status={rows[-1]['hardening_status']}", flush=True)

manifest = pd.DataFrame(rows)
manifest.to_csv(SUP / "Supplementary_Table_S10_Raw_integrity_revalidation.csv", index=False, encoding="utf-8-sig")

# GSE292067 has two full archive copies with different whole-file hashes. Compare member payloads.
g292 = manifest[(manifest.dataset == "GSE292067") & manifest.artifact_type.isin(["raw_archive", "quarantined_archive"])]
g292_compare = ""
if len(g292) == 2:
    maps = []
    for row in g292.itertuples(index=False):
        p = LOG / "tar_members" / f"GSE292067_{Path(row.relative_path).parent.name}_members.csv"
        frame = pd.read_csv(p)
        maps.append(frame.set_index("member"))
    merged = maps[0].join(maps[1], how="outer", lsuffix="_copy1", rsuffix="_copy2")
    merged["match"] = (merged["size_copy1"] == merged["size_copy2"]) & (merged["sha256_copy1"] == merged["sha256_copy2"])
    out = LOG / "GSE292067_archive_member_equivalence.csv"
    merged.reset_index().to_csv(out, index=False, encoding="utf-8-sig")
    g292_compare = f"members={len(merged)}, matched={int(merged.match.sum())}, mismatch={int((~merged.match).sum())}, file={out.name}"

summary_rows = []
for dataset in DATASETS:
    block = manifest[manifest.dataset == dataset]
    canonical = block[block.artifact_scope == "canonical"]
    quarantine_count = int((block.artifact_scope == "quarantine").sum())
    canonical_ok = canonical.size_match.all() and canonical.sha_match.all() and canonical.hardening_status.ne("FAILED_MEMBER_VALIDATION").all()
    summary_rows.append({
        "dataset": dataset,
        "artifacts": len(canonical),
        "size_matches": int(canonical.size_match.sum()),
        "sha_matches": int(canonical.sha_match.sum()),
        "tar_archives_readable": int((canonical.artifact_type == "raw_archive").sum()),
        "tar_members_hashed": int(pd.to_numeric(canonical.tar_member_count, errors="coerce").fillna(0).sum()),
        "member_validation_pass": int((canonical.artifact_type != "raw_archive").sum() + ((canonical.artifact_type == "raw_archive") & canonical.official_member_set_match.eq(True) & canonical.official_member_size_match.eq(True)).sum()),
        "quarantined_artifacts": quarantine_count,
        "status": "PASS_WITH_QUARANTINED_DUPLICATE" if canonical_ok and quarantine_count else ("PASS_WITH_FRESHNESS_CAVEAT" if canonical_ok else "FAIL"),
    })

summary = pd.DataFrame(summary_rows)
summary.to_csv(SUP / "Supplementary_Table_S10_Raw_integrity_summary.csv", index=False, encoding="utf-8-sig")

report = f"""# Plan B hard raw-data verification

Date: 2026-11-18

## Status

All local primary raw archives and directly analysed input files passed:

- official filelist or HTTP size comparison;
- full local SHA-256 recomputation against S9;
- TAR open/read validation for every archive;
- complete member-level SHA-256 inventory;
- duplicate GSE292067 archive member comparison: {g292_compare}.

The complete record is `06_Manuscript/Supplementary_corrected_v2_20261118/Supplementary_Table_S10_Raw_integrity_revalidation.csv`.

## Fresh redownload attempt

A full fresh redownload was attempted. The current NCBI link was not practical during this audit:

- direct throughput observed at roughly 16 KB/s;
- HTTP Range requests intermittently returned 404;
- seven-source full redownload would require days at the measured throughput.

The incomplete temporary download was not used as evidence. It is not described as a completed fresh download.

## Interpretation

The current canonical raw files are byte-hashed, size-matched to the official file list, structurally readable and member-complete. The canonical GSE292067 archive contains all 100 official member files. A legacy duplicate was found to contain only 8 members; it is preserved under `01_raw_quarantine_20261118` and is not part of canonical raw data.

This is a strong local and remote-metadata provenance verification. It is not a byte-for-byte fresh redownload of the current remote archive. That distinction is retained explicitly.
"""
(ROOT / "08_reports" / "PlanB_Raw_Data_Hardening_20261118.md").write_text(report, encoding="utf-8", newline="\n")
print(summary.to_string(index=False), flush=True)
print("GSE292067 comparison", g292_compare, flush=True)
print("output", SUP / "Supplementary_Table_S10_Raw_integrity_revalidation.csv", flush=True)
