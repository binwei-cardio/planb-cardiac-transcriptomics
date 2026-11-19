# Plan B zero-residual provenance audit

Date: 2026-11-18  
Scope: control-gene export, portable paths and complete raw-file SHA-256 inventory

## Status

The three requested residual provenance items are closed. The latest synchronized validation passes 33/33 checks. No Table 2 effect size, p value or FDR was changed.

## 1. Complete control-gene export

Primary files:

- `06_Manuscript/Supplementary_corrected_v2_20261118/Supplementary_Table_S8_Control_gene_selections.csv`
- `06_Manuscript/Supplementary_corrected_v2_20261118/Supplementary_Table_S8_Control_gene_summary.csv`

Coverage:

- 47,949 selected control-gene rows;
- 438 sample-by-programme summaries;
- 65 sample or group scoring units;
- seven datasets;
- no duplicate control gene within a dataset, sample and programme;
- fixed seed 42, 20 average-expression bins and at most 10 controls per programme gene.

Dataset coverage:

| Dataset | Scoring units | Sample-by-programme rows |
|---|---:|---:|
| GSE292067 | 25 | 175 |
| GSE298023 | 13 | 78 |
| GSE297745 | 4 | 24 |
| GSE299032 | 5 | 35 |
| GSE135805 | 4 | 28 |
| GSE161470 | 2 | 14 |
| GSE288222 | 12 | 84 |

GSE161470 uses group-level control selection by design. GSE135805 records Ensembl gene identifiers after symbol mapping. Modules with fewer than three detected programme genes are marked `NOT_SCORED_OR_INSUFFICIENT_GENES`.

## 2. Portable path parameterization

- `planb_paths.py` derives `PLANB_ROOT` from the script location.
- `PLANB_ROOT` can override the Plan B repository root.
- `PLANB_PROJECT_ROOT` can override the parent project root.
- All 57 Python scripts compile successfully.
- Static scanning found zero hard-coded drive paths.
- A representative downstream script was rerun successfully after parameterization.

## 3. Complete raw-file SHA-256 inventory

Primary files:

- `06_Manuscript/Supplementary_corrected_v2_20261118/Supplementary_Table_S9_Raw_file_SHA256.csv`
- `06_Manuscript/Supplementary_corrected_v2_20261118/Supplementary_Table_S9_Raw_file_summary.csv`

Coverage:

- 70 files under `01_raw`;
- 5,542,396,236 bytes;
- SHA-256, size, UTC modification time and status class for every file;
- complete archives, preserved source files, partial or transfer artifacts, logs and metadata are included;
- 70/70 current files rehashed with zero mismatches.

## 4. Archive member revalidation

S10 revalidates the canonical raw archives against official member inventories:

- 13 canonical artifacts and 240 canonical TAR members hashed;
- all canonical archive member names and sizes match the official file list;
- GSE292067 canonical archive: 100/100 members pass;
- one legacy GSE292067 duplicate with 8/100 members is quarantined under `01_raw_quarantine_20261118` and excluded from canonical raw data.

The failed full fresh-download probe is recorded separately in `08_reports/PlanB_Raw_Data_Hardening_20261118.md`; it is not counted as a completed download.

## 5. Package integrity

- Supplementary manifest: 106 entries;
- corrected project snapshot: 106 entries;
- manifest and snapshot are identical;
- 106/106 Supplementary files match recorded size and SHA-256;
- post-audit validation: 33/33 PASS.

## Residual source-state caveats

The following are source-history facts, not missing provenance records:

1. GSE161470 has one failing heart and one Control pseudobulk group.
2. The GSE292067 whole-TAR hash differs from an older reference because NCBI regenerated archive headers; 100/100 extracted files matched.
3. Some raw TARs were preserved from earlier downloads rather than freshly redownloaded.
4. S9 includes interrupted or partial transfer artifacts and labels them explicitly; their hashes do not imply download completeness.
5. A legacy GSE292067 archive duplicate is quarantined because only 8 of 100 official members were present.

## Audit artifacts

- Audit remediation: `08_reports/PlanB_Supplementary_Audit_Remediation_20261118.md`
- Post-audit validation: `08_reports/PlanB_PostAudit_Validation_20261118.md`
- Corrected Supplementary snapshot: `08_reports/PlanB_Supplementary_SHA256_snapshot_corrected_20261118.csv`
- Reproducibility rules: `REPRO_RULES.md`
