# Plan B post-audit validation

- Checks: 33
- PASS: 33
- FAIL: 0

| Check | Status | Detail |
|---|---|---|
| English references | PASS | count=40, uncited=[], out_of_range=[] |
| Chinese references | PASS | count=40, uncited=[], out_of_range=[] |
| English Table 2 values in Results | PASS | [] |
| Chinese Table 2 values in Results | PASS | [] |
| English freeze label count | PASS | 5 |
| Chinese freeze label count | PASS | 5 |
| Mouse causal boundary | PASS |  |
| DoxCM/NICM negative result | PASS |  |
| TCM future-only boundary | PASS |  |
| S1 GEO selection fields | PASS |  |
| S1 critical sample-selection disclosures | PASS | GSE298023=13/18; GSE299032=5/30 |
| GSE135805 S1 panel wording | PASS |  |
| GSE135805 corrected labels | PASS | {'GSM4030472': 'Normal', 'GSM4030473': 'ICM', 'GSM4030474': 'DCM', 'GSM4030475': 'HCM'} |
| S5 completeness and concordance | PASS | rows=144, counts={'Rank-based': 72, 'Z-score': 72}, concordance={'Rank-based': 45, 'Z-score': 45} |
| S5 manuscript synchronization | PASS |  |
| S6 supplemental Senescence completeness | PASS | rows=13, counts={'GSE297745': 1, 'GSE298023': 12} |
| S6 manuscript synchronization | PASS |  |
| S7 exploratory seven-programme matrix | PASS | shape=(7, 7), modules=['Fibrosis_ECM', 'Tcell_cytotoxic', 'CM_stress', 'Inflammation', 'Senescence', 'Hypoxia_Metabolism', 'Endothelial'] |
| S7 manuscript synchronization | PASS |  |
| Stale alternative-scoring statements removed | PASS | [] |
| S8 complete control-gene export | PASS | detail_rows=47949, units={'GSE135805': 4, 'GSE161470': 2, 'GSE288222': 12, 'GSE292067': 25, 'GSE297745': 4, 'GSE298023': 13, 'GSE299032': 5}, summary_rows={'GSE135805': 28, 'GSE161470': 14, 'GSE288222': 84, 'GSE292067': 175, 'GSE297745': 24, 'GSE298023': 78, 'GSE299032': 35}, duplicates=0 |
| S8 manuscript and guide synchronization | PASS |  |
| S9 complete raw-file SHA-256 inventory | PASS | rows=70, actual_files=70, bytes=5542396236, mismatches=[] |
| S9 manuscript and guide synchronization | PASS |  |
| S10 official archive-member and quarantine validation | PASS | rows=14, canonical=13, canonical_members=240, quarantine_members=8 |
| S10 manuscript, guide and hardening report synchronization | PASS |  |
| Path parameterization | PASS | scripts=57, drive_hits=[], compile_errors=[] |
| Portable-path manuscript and guide synchronization | PASS |  |
| Manifest file set complete | PASS | manifest=106, actual=106, missing=[], extra=[] |
| Manifest and corrected snapshot match | PASS | manifest_rows=106, snapshot_rows=106 |
| Corrected Supplementary SHA snapshot | PASS | entries=106, mismatches=[] |
| Remediation report synchronized | PASS |  |
| Submission readiness synchronized | PASS |  |
