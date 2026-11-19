# Plan B hard raw-data verification

Date: 2026-11-18

## Status

All local primary raw archives and directly analysed input files passed:

- official filelist or HTTP size comparison;
- full local SHA-256 recomputation against S9;
- TAR open/read validation for every archive;
- complete member-level SHA-256 inventory;
- duplicate GSE292067 archive member comparison: members=100, matched=7, mismatch=93, file=GSE292067_archive_member_equivalence.csv.

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
