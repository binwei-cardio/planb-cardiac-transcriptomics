# Plan B raw-data provenance and authenticity audit

Date: 2026-11-18

## What this audit establishes

- Every local raw file was hashed with SHA-256.
- Tar archives were compared by byte size with the current NCBI filelist where available.
- Analysis outputs were compared with the original outputs and are listed separately from download provenance.
- Fresh download, preserved-raw reuse and unresolved source-link cases are distinguished explicitly.

## Dataset summary

| Dataset | Files | Bytes | Remote size | Download mode | File-level evidence | Output comparison | Authenticity status |
|---|---:|---:|---|---|---|---|---|
| GSE292067 | 1 | 1634324480 | PASS | Fresh remote range download; one corrupt resume segment repaired from NCBI | 100/100 extracted files matched prior known-good copy | 7/7 outputs PASS | VERIFIED_WITH_CAVEAT |
| GSE161470 | 4 | 22933431 | PASS | Preserved processed input; exact NCBI source URL re-confirmed 2026-11-18 | Local SHA256; remote size; first 64 KiB byte match | 3/3 outputs PASS | VERIFIED_SOURCE_RECORD_CLOSED |
| GSE288222 | 1 | 141844480 | PASS | Preserved NCBI raw TAR from prior clean-room setup | No fresh re-download performed; size matches current NCBI filelist | 6/6 outputs PASS | VERIFIED_SOURCE_WITH_LIMITED_FRESHNESS |
| GSE298023 | 1 | 1940602880 | PASS | Preserved prior NCBI raw TAR copied into clean-room directory | 54/54 extracted files matched prior raw directory | 8/8 core outputs PASS | VERIFIED_WITH_FRESHNESS_CAVEAT |
| GSE297745 | 1 | 323297280 | PASS | Preserved NCBI raw TAR from prior clean-room setup | No fresh re-download performed; size matches current NCBI filelist | 4/4 outputs PASS | VERIFIED_SOURCE_WITH_LIMITED_FRESHNESS |
| GSE299032 | 1 | 297123840 | PASS | Preserved NCBI raw TAR from prior clean-room setup | No fresh re-download performed; size matches current NCBI filelist | 5/5 outputs PASS | VERIFIED_SOURCE_WITH_LIMITED_FRESHNESS |
| GSE135805 | 4 | 721828 | PASS | Freshly downloaded in this audit session | 4/4 raw files matched prior local copies by SHA256 | 3/3 outputs PASS | VERIFIED_FRESH |

## Explicit limitations

- **GSE292067:** the whole TAR SHA-256 does not match the old reference; 100/100 extracted member files match. This is a real archive-container discrepancy, not reported as a whole-file pass.
- **GSE298023:** the preserved NCBI raw TAR was used; it was not freshly downloaded in full during this audit. Its size matches the current NCBI filelist and its SHA-256 is recorded.
- **GSE161470:** the four processed count/metadata files were located at their exact NCBI GEO supplementary URLs. Remote size and Last-Modified metadata match the local files, and the first 64 KiB of every file is byte-identical. Full-file re-download was not performed, but the source record is now closed.
- **GSE288222, GSE297745 and GSE299032:** preserved NCBI raw TARs were used. Their sizes match current NCBI filelists, but they were not independently re-downloaded in this audit.
- **GSE135805:** all four sample-level files were freshly downloaded and matched prior local copies by SHA-256.

## Original data locations

- Clean-room raw: `G:\Codex所有文件\ChatGPT\心脏肿瘤学\PlanB_Repro_v1\01_raw`
- Extracted data: `G:\Codex所有文件\ChatGPT\心脏肿瘤学\PlanB_Repro_v1\02_unpacked`
- Existing project raw data: `G:\Codex所有文件\ChatGPT\心脏肿瘤学\生信先行_方案B\data`

## Package boundary

The reproducibility ZIP contains scripts, output tables, figures, comparison reports and manifests, but not the multi-gigabyte raw data. Raw data remain in the project directories listed above.

## Complete-file SHA-256 inventory addendum

The complete inventory is now `06_Manuscript/Supplementary_corrected_v2_20261118/Supplementary_Table_S9_Raw_file_SHA256.csv`. It covers every existing file under `01_raw`, not only the seven primary dataset inputs:

- 70 files;
- 5,542,396,236 bytes;
- complete archives, preserved source files, partial or transfer artifacts, logs and metadata;
- SHA-256, size, UTC modification time and status class for each file;
- 70/70 files independently rehashed with zero mismatches.

The compact dataset-level totals are in `Supplementary_Table_S9_Raw_file_summary.csv`. A legacy GSE292067 archive duplicate with 8/100 members was moved to `01_raw_quarantine_20261118` and is not counted as canonical raw data.

