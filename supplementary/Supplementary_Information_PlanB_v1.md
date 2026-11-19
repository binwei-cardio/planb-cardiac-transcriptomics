# Supplementary Information: Plan B candidate recurrent programmes in heart failure and cancer therapy-related cardiotoxicity

## Supplementary Table S1. Datasets, sample selection and evidence roles

Files:
- `Supplementary_Table_S1_Datasets.csv`
- `Supplementary_Table_S1_Module_availability.csv`

S1 records total GEO GSM counts, GSMs used, excluded or unavailable samples, assessed programmes and interpretation boundaries. GSE298023 used 13/18 GSMs and excluded five ICM-scar samples; GSE299032 used five heart scRNA-seq GSMs from a 30-GSM series; GSE292067 processed matrices were used because nine GEO samples lacked raw files. GSE297745 and GSE299032 are descriptive and directional only.

## Supplementary Table S2. Programme gene lists

File: `Supplementary_Table_S2_Module_genes.csv`

The table lists requested human symbols and mouse symbols used where applicable. CXCL8 has no direct one-to-one mouse ortholog and is marked NA. Gene overlap across programmes (CCL5, IFNG, IL6 and VEGFA) means that programmes are not fully independent evidence streams.

## Supplementary Table S3. Spatial programme architecture in mouse ICI myocarditis

Files:
- `Supplementary_Table_S3_Spatial_niche_full.csv`
- `Supplementary_Table_S3_Moran_I_summary.csv`
- `Supplementary_Table_S3_Neighbourhood_summary.csv`

S3 contains six programmes. Senescence was not spatially analysed. The mouse Visium design is 2-versus-2; results are descriptive and directional only, and no causal inference is possible.

## Supplementary Table S4. Sensitivity analyses

Files:
- `Supplementary_Table_S4A_GSE161470_directional.csv`
- `Supplementary_Table_S4B_GSE135805_section_summary.csv`
- `Supplementary_Table_S4C_GSE135805_gene_coverage.csv`
- `Supplementary_Table_S4_Sensitivity_summary.csv`

GSE135805 labels were corrected against GEO: GSM4030473 = ICM and GSM4030475 = HCM. Its section-specific gene coverage ranges from 4,029 to 12,734 genes. GSE161470 contains one failing heart; its four control records were collapsed to one Control pseudobulk group and the table is descriptive only. Neither dataset is used for primary inference.

## Supplementary Table S5. Alternative scoring sensitivity

Files:
- `Supplementary_Table_S5A_Zscore_pseudobulk.csv`
- `Supplementary_Table_S5B_Rank_score_pseudobulk.csv`
- `Supplementary_Table_S5_Alternative_scoring_tests.csv`

A focused z-score and rank-based analysis was performed in GSE292067 for four key programmes (Fibrosis-ECM, Cytotoxic-T, CM_stress and Senescence), six cell types and three comparisons. Directional concordance with the primary control-gene score was 45/72 for each alternative method. These analyses are partial sensitivity checks and do not replace the primary Table 2 results.

## Supplementary Table S6. Senescence sensitivity in GSE298023 and GSE297745

Files:
- `Supplementary_Table_S6A_GSE298023_Senescence_pseudobulk.csv`
- `Supplementary_Table_S6B_GSE297745_Senescence_pseudobulk.csv`
- `Supplementary_Table_S6_Senescence_sensitivity_tests.csv`

Senescence was added as a supplemental analysis for the two datasets whose primary scoring scripts did not include it. The GSE298023 comparisons are donor-limited (n = 2). The GSE297745 result is a 2-versus-2 descriptive comparison and cannot support causal inference.

## Supplementary Table S7. Seven-programme cross-dataset sensitivity matrix

Files:
- `Supplementary_Table_S7_Seven_programme_cross_dataset_matrix.csv`
- `Supplementary_Table_S7_Seven_programme_cross_dataset_qvalues.csv`
- `Supplementary_Table_S7_Seven_programme_cross_dataset_evidence_tier.csv`

This supplemental matrix adds Endothelial to the six-programme primary synthesis. Endothelial was not directionally consistent across the seven exploratory contrasts. S7 is exploratory and does not replace the frozen Figure 5 or Table 2.

## Supplementary Table S8. Complete control-gene selection export

Files:
- `Supplementary_Table_S8_Control_gene_selections.csv`
- `Supplementary_Table_S8_Control_gene_summary.csv`

S8 records 47949 selected control-gene rows across 65 sample or group scoring units and 438 sample-by-programme summaries. Selections used 20 average-expression bins, seed 42 and at most 10 control genes per programme gene. GSE161470 controls are group-level by design; GSE135805 control identifiers are Ensembl gene IDs after symbol mapping. Modules with fewer than three detected programme genes are explicitly marked as not scored.

## Supplementary Table S9. Complete raw-file SHA-256 inventory

Files:
- `Supplementary_Table_S9_Raw_file_SHA256.csv`
- `Supplementary_Table_S9_Raw_file_summary.csv`

S9 lists all 70 files currently under `01_raw`, totalling 5,542,396,236 bytes, with relative path, size, UTC modification time, file class and SHA-256. The inventory includes complete archives, preserved source files, partial or transfer artifacts, logs and metadata. A hash confirms file identity, not download completeness; the `status_class` column distinguishes these states explicitly.

## Supplementary Table S10. Hard raw-data revalidation

Files:
- `Supplementary_Table_S10_Raw_integrity_revalidation.csv`
- `Supplementary_Table_S10_Raw_integrity_summary.csv`

S10 contains 14 artifact records: 13 canonical artifacts and 1 quarantined duplicate. Canonical raw archives were checked against official member names and sizes, and 240 canonical TAR members were hashed individually. The GSE292067 canonical archive passed with 100 members; a legacy duplicate with only 8 members is preserved under `01_raw_quarantine_20261118` and is not used as a raw input.

## Core tables and code

`Supplementary_Core_Tables/` contains the principal pseudobulk, permutation, FDR, synthesis and spatial tables. `Supplementary_Code/` contains the analysis scripts, `planb_paths.py`, the control-gene exporter, the raw-file hashing script and the deterministic finalizer. `REPRO_RULES.md` describes the clean-room rules. The archived source audit and reproducibility reports remain in the parent project.

## Statistical and interpretation notes

- Table 2 uses `gse292067_celltype_permutation.csv` as the primary source for the GSE292067 FDR values; `planb_master_module_tests_v4.csv` applies a different correction family for cross-dataset synthesis.
- The primary cross-dataset synthesis includes six programmes. Endothelial is included only in the exploratory S7 matrix.
- Alternative z-score and rank-based scoring were evaluated in a focused GSE292067 sensitivity analysis (S5). Partial directional concordance means that these scores do not replace the primary control-gene score.
- The DoxCM-versus-NICM comparison is a negative result: no direct comparison survived FDR correction.
- Mouse datasets are descriptive and directional only; no causal inference is made.
- TCM content is restricted to future research hypotheses; no efficacy inference is made.
- `Supplementary_SHA256_manifest.csv` lists every file in this directory except the manifest itself; the matching project snapshot is stored under `08_reports/`.
