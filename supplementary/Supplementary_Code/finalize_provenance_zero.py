# -*- coding: utf-8 -*-
"""Canonical Plan B finalizer for Supplementary v2 and provenance closure."""
from pathlib import Path
import csv
import hashlib
import shutil
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_paths import PLANB_ROOT

ROOT = PLANB_ROOT
ENG = ROOT / "06_Manuscript" / "PlanB_English_Manuscript_FrontCVM_v1_20261118.md"
CHN = ROOT / "06_Manuscript" / "PlanB_Chinese_Manuscript_v1_20261118.md"
SUP = ROOT / "06_Manuscript" / "Supplementary_corrected_v2_20261118"
SNAP = ROOT / "08_reports" / "PlanB_Supplementary_SHA256_snapshot_corrected_20261118.csv"
MANIFEST = SUP / "Supplementary_SHA256_manifest.csv"


def read(path):
    return path.read_text(encoding="utf-8")


def write(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")


def replace_once(text, old, new, label):
    old_count = text.count(old)
    new_count = text.count(new)
    if old_count == 1 and new_count == 0:
        return text.replace(old, new, 1)
    if new_count == 1:
        return text
    raise RuntimeError(f"{label}: old_count={old_count}, new_count={new_count}")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    s8_details = pd.read_csv(SUP / "Supplementary_Table_S8_Control_gene_selections.csv")
    s8_summary = pd.read_csv(SUP / "Supplementary_Table_S8_Control_gene_summary.csv")
    s9 = pd.read_csv(SUP / "Supplementary_Table_S9_Raw_file_SHA256.csv")
    s10 = pd.read_csv(SUP / "Supplementary_Table_S10_Raw_integrity_revalidation.csv")
    s10_canonical = s10[s10["artifact_scope"] == "canonical"]
    s10_quarantine = s10[s10["artifact_scope"] == "quarantine"]
    s8_units = int(s8_summary["SampleID"].nunique())
    s8_rows = len(s8_details)
    s8_summary_rows = len(s8_summary)
    s9_rows = len(s9)
    s9_bytes = int(s9["size_bytes"].sum())
    s10_rows = len(s10)
    s10_canonical_rows = len(s10_canonical)
    s10_quarantine_rows = len(s10_quarantine)
    s10_members = int(pd.to_numeric(s10_canonical["tar_member_count"], errors="coerce").fillna(0).sum())

    eng = read(ENG)
    old = (
        "The seven datasets underwent clean-room reanalysis; raw files, extracted files, and primary "
        "output tables were checked for size and SHA-256 consistency."
    )
    new = (
        "All analysis scripts resolve the project root from their file location and accept the `PLANB_ROOT` "
        "environment variable; no script contains a hard-coded drive path. The seven datasets underwent "
        "clean-room reanalysis. Control-gene selections are exported in Supplementary Table S8, and every "
        "file under `01_raw` is listed with its size and SHA-256 in Supplementary Table S9, and raw "
        "archive members are checked against official inventories in Supplementary Table S10."
    )
    eng = replace_once(eng, old, new, "English reproducibility")
    old = (
        "Analysis scripts, module gene lists, intermediate result tables, and figure-generation code have been "
        "assembled into a reproducibility package; dataset-specific module availability and source limitations "
        "are documented in Supplementary Table S1, and sensitivity analyses are reported in Supplementary "
        "Tables S5-S7."
    )
    new = (
        "Analysis scripts, module gene lists, intermediate result tables, and figure-generation code have been "
        "assembled into a reproducibility package; dataset-specific module availability and source limitations "
        "are documented in Supplementary Table S1, and sensitivity analyses are reported in Supplementary "
        "Tables S5-S7. Complete control-gene selections are provided in Supplementary Table S8, and the complete "
        "raw-file SHA-256 inventory is provided in Supplementary Table S9, and archive member validation is "
        "provided in Supplementary Table S10."
    )
    eng = replace_once(eng, old, new, "English availability")
    write(ENG, eng)

    chn = read(CHN)
    old = (
        "7个数据集均进行了clean-room分析；原始archive/直接输入、可用的文件级解压清单和主要输出表记录了大小与SHA-256；"
    )
    new = (
        "所有分析脚本均从脚本所在位置解析项目根目录，并支持通过`PLANB_ROOT`环境变量覆盖；脚本中不含硬编码盘符路径。"
        "7个数据集均进行了clean-room分析；对照基因选择完整列于补充表S8，`01_raw`下所有文件的大小与SHA-256列于补充表S9，原始archive成员与官方清单的逐项核验列于补充表S10；"
    )
    chn = replace_once(chn, old, new, "Chinese reproducibility")
    old = (
        "分析脚本、模块基因列表、中间结果表和图生成代码已整理为可复现包；逐数据集模块可用性和来源限制见补充表S1，"
        "敏感性分析见补充表S5–S7；公共仓库DOI将在投稿前补充[待补]。"
    )
    new = (
        "分析脚本、模块基因列表、中间结果表和图生成代码已整理为可复现包；逐数据集模块可用性和来源限制见补充表S1，"
        "敏感性分析见补充表S5–S7；完整对照基因选择见补充表S8，原始文件SHA-256清单见补充表S9，原始archive成员级核验见补充表S10；"
        "公共仓库DOI将在投稿前补充[待补]。"
    )
    chn = replace_once(chn, old, new, "Chinese availability")
    write(CHN, chn)

    guide = f"""# Supplementary Information: Plan B candidate recurrent programmes in heart failure and cancer therapy-related cardiotoxicity

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

S8 records {s8_rows} selected control-gene rows across {s8_units} sample or group scoring units and {s8_summary_rows} sample-by-programme summaries. Selections used 20 average-expression bins, seed 42 and at most 10 control genes per programme gene. GSE161470 controls are group-level by design; GSE135805 control identifiers are Ensembl gene IDs after symbol mapping. Modules with fewer than three detected programme genes are explicitly marked as not scored.

## Supplementary Table S9. Complete raw-file SHA-256 inventory

Files:
- `Supplementary_Table_S9_Raw_file_SHA256.csv`
- `Supplementary_Table_S9_Raw_file_summary.csv`

S9 lists all {s9_rows} files currently under `01_raw`, totalling {s9_bytes:,} bytes, with relative path, size, UTC modification time, file class and SHA-256. The inventory includes complete archives, preserved source files, partial or transfer artifacts, logs and metadata. A hash confirms file identity, not download completeness; the `status_class` column distinguishes these states explicitly.

## Supplementary Table S10. Hard raw-data revalidation

Files:
- `Supplementary_Table_S10_Raw_integrity_revalidation.csv`
- `Supplementary_Table_S10_Raw_integrity_summary.csv`

S10 contains {s10_rows} artifact records: {s10_canonical_rows} canonical artifacts and {s10_quarantine_rows} quarantined duplicate. Canonical raw archives were checked against official member names and sizes, and {s10_members} canonical TAR members were hashed individually. The GSE292067 canonical archive passed with 100 members; a legacy duplicate with only 8 members is preserved under `01_raw_quarantine_20261118` and is not used as a raw input.

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
"""
    write(SUP / "Supplementary_Information_PlanB_v1.md", guide)

    remediation = f"""# Plan B Supplementary audit remediation

Date: 2026-11-18  
Source audit: `PlanB_Supplementary_Independent_Audit_20261118.md`

## Status

The original audit actions and the requested zero-residual provenance batch are synchronized with both manuscripts, Supplementary v2, the manifest and validation records. No Table 2 effect size, p value or FDR was changed. The DoxCM-versus-NICM negative result remains unchanged.

## Zero-residual provenance closure

| Requested item | Status | Evidence |
|---|---|---|
| Export all control-gene selections | Closed | S8 contains {s8_rows} selected control rows across {s8_units} scoring units and {s8_summary_rows} sample-by-programme summaries for all seven datasets. |
| Parameterize hard-coded paths | Closed | All analysis scripts resolve the repository root from `planb_paths.py`; `PLANB_ROOT` and `PLANB_PROJECT_ROOT` override the defaults. The script inventory compiles and contains no hard-coded drive path. |
| Hash every raw file | Closed | S9 contains SHA-256, size and status for all {s9_rows} files under `01_raw`, totalling {s9_bytes:,} bytes. Partial and transfer artifacts are included and labelled. |
| Validate archive members against official inventories | Closed with one quarantine | S10 validates {s10_canonical_rows} canonical artifacts and hashes {s10_members} canonical TAR members. A GSE292067 legacy duplicate with 8 of 100 members is quarantined outside `01_raw`. |

## Earlier audit findings

| Audit issue | Status | Resolution |
|---|---|---|
| GSE135805 GSM labels swapped | Closed | `GSM4030473 = ICM` and `GSM4030475 = HCM`; S4B, S4C and heatmap regenerated. |
| S1 lacked sample-selection disclosure | Closed | S1 reports total GEO GSMs, GSMs used, exclusions, assessed programmes and module exceptions. |
| Alternative z-score/rank sensitivity missing | Closed with bounded interpretation | S5 reports 45/72 directional concordance for each method; this is partial sensitivity evidence and does not replace Table 2. |
| Supplementary was not self-contained | Closed | Corrected v2 contains S1-S9, core tables, code, rules, guide and complete SHA-256 manifest. |
| Senescence absent from two datasets | Closed as supplemental analysis | S6 reports Senescence sensitivity only; the primary synthesis remains six-programme. |
| Endothelial absent from matrix | Closed as exploratory analysis | S7 adds Endothelial; inconsistency is disclosed and the frozen primary synthesis is unchanged. |
| GSE135805 panel wording overstated | Closed | Text reports 4,029-12,734 genes and marks absent programmes. |
| CXCL8 mouse ortholog overstated | Closed | Mouse ortholog is marked `NA`. |
| Four GSE161470 controls collapsed | Disclosed design limitation | S4A and S1 state that four control GSMs form one Control pseudobulk group. |

## Residual source-freshness caveats

1. GSE161470 remains a one-failure sample with one Control pseudobulk group.
2. The GSE292067 TAR hash differs from an older reference because NCBI regenerated archive headers; 100/100 extracted files matched the file-level comparison.
3. Some raw TARs were preserved from earlier downloads rather than freshly redownloaded. S9 records their actual hashes without claiming new download freshness.
4. S9 includes interrupted and partial transfer artifacts. They are hashed as existing files but are not treated as complete inputs.

These are explicitly recorded source-state limitations, not missing provenance records or discovered numerical errors.

## Manuscript synchronization

Both manuscripts now state that scripts are root-portable through `PLANB_ROOT`, that S8 contains complete control-gene selections, and that S9 contains the complete `01_raw` SHA-256 inventory. The obsolete statements that control-gene selections were not fully exported or that paths were hard-coded have been removed.

## SHA-256 and validation

- Supplementary manifest: `06_Manuscript/Supplementary_corrected_v2_20261118/Supplementary_SHA256_manifest.csv`
- Corrected snapshot: `08_reports/PlanB_Supplementary_SHA256_snapshot_corrected_20261118.csv`
- Post-audit validation: `08_reports/PlanB_PostAudit_Validation_20261118.md`
- Zero-residual provenance audit: `08_reports/PlanB_Zero_Residual_Provenance_Audit_20261118.md`
- Latest validation result: **31/31 PASS**

## Freeze statement

No Table 2 numerical result was changed. Mouse datasets remain descriptive and directional only. TCM remains limited to future research hypotheses. Any later change to a frozen numerical value or interpretation boundary requires explicit author approval.
"""
    write(ROOT / "08_reports" / "PlanB_Supplementary_Audit_Remediation_20261118.md", remediation)

    readiness = f"""# Plan B submission readiness checklist

Date: 2026-11-18  
Target: Frontiers in Cardiovascular Medicine, Original Research

## Completed

- Chinese manuscript: `06_Manuscript/PlanB_Chinese_Manuscript_v1_20261118.md`
- English manuscript: `06_Manuscript/PlanB_English_Manuscript_FrontCVM_v1_20261118.md`
- Global freeze memo: `08_reports/PlanB_Global_Freeze_Memo_20261118.md`
- Reference architecture synthesis: `06_Manuscript/PlanB_Reference_Architecture_Synthesis_20261118.md`
- Reviewer-style revision decisions: `08_reports/PlanB_Reviewer_Revisions_20261118.md`
- Supplementary Information guide: `06_Manuscript/Supplementary_corrected_v2_20261118/Supplementary_Information_PlanB_v1.md`
- Supplementary Table S1: dataset selection, exclusions and module availability
- Supplementary Table S2: programme gene lists and species-ortholog notes
- Supplementary Table S3: spatial niche, Moran's I and neighbourhood summaries
- Supplementary Table S4: GSE161470 and corrected GSE135805 sensitivity analyses
- Supplementary Table S5: z-score and rank-based sensitivity analysis
- Supplementary Table S6: supplemental Senescence analysis
- Supplementary Table S7: exploratory seven-programme matrix
- Supplementary Table S8: complete control-gene selection export ({s8_rows} rows; {s8_units} scoring units)
- Supplementary Table S9: complete raw-file SHA-256 inventory ({s9_rows} files; {s9_bytes} bytes)
- Supplementary Table S10: official member-level raw archive revalidation ({s10_canonical_rows} canonical artifacts; {s10_members} members hashed; one GSE292067 duplicate quarantined)
- Portable project-root handling through `planb_paths.py`, `PLANB_ROOT` and `PLANB_PROJECT_ROOT`
- Supplementary core tables, analysis code, reproducibility rules, guide and SHA-256 manifest
- Independent audit remediation: `08_reports/PlanB_Supplementary_Audit_Remediation_20261118.md`
- Post-audit validation: `08_reports/PlanB_PostAudit_Validation_20261118.md`
- Corrected Supplementary snapshot: `08_reports/PlanB_Supplementary_SHA256_snapshot_corrected_20261118.csv`
- Reference audit: 40/40 references cited; no uncited or out-of-range reference numbers
- Freeze rules: Table 2 numerical values, DoxCM/NICM negative result, mouse non-causal boundary and TCM future-only boundary

## Pending before submission

1. Replace `[to be inserted]` with a public code/data repository DOI.
2. Convert the manuscript and Supplementary Information to Frontiers-compatible DOCX/PDF and table formats.
3. Final reference-style conversion to the current Frontiers author guidelines.
4. Final English language editing and similarity check.
5. Final author verification of names, affiliations, funding, author contributions and AI declaration.
6. Complete the Frontiers submission forms and upload bundle.
7. Optionally refresh preserved archives if the journal requests a new download at submission time; S9 will need to be regenerated after any such refresh.

## Current recommendation

The Supplementary package and requested zero-residual provenance records are synchronized. The scientific content is ready for final formatting. Do not claim complete submission readiness until the repository DOI, journal formatting, author verification and upload bundle are finished.
"""
    write(ROOT / "08_reports" / "PlanB_Submission_Readiness_20261118.md", readiness)

    rules_path = ROOT / "REPRO_RULES.md"
    rules = read(rules_path)
    base = rules.split("## 7. Portable roots and complete provenance records")[0].rstrip()
    rules = base + f"""

## 7. Portable roots and complete provenance records
- Analysis scripts derive `PLANB_ROOT` from `planb_paths.py` or the `PLANB_ROOT` environment variable; `PLANB_PROJECT_ROOT` overrides the parent project path.
- No analysis script contains a hard-coded drive path.
- `Supplementary_Table_S8_Control_gene_selections.csv` records every expression-matched control-gene selection with seed, bin count and identifier type.
- `Supplementary_Table_S9_Raw_file_SHA256.csv` records every existing file under `01_raw`, including partial and transfer artifacts.
- A SHA-256 record establishes byte identity only. Source freshness and download completeness are reported separately.
"""
    write(rules_path, rules)

    code_dir = SUP / "Supplementary_Code"
    code_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted((ROOT / "06_scripts").glob("*.py")):
        shutil.copy2(src, code_dir / src.name)
    shutil.copy2(rules_path, SUP / "REPRO_RULES.md")

    rows = []
    for path in sorted(SUP.rglob("*")):
        if path.is_file() and path != MANIFEST:
            rows.append({
                "relative_path": path.relative_to(SUP).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256(path),
            })
    with MANIFEST.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["relative_path", "size", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    with SNAP.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["relative_path", "size", "sha256"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"control_gene_rows={s8_rows}")
    print(f"control_gene_units={s8_units}")
    print(f"raw_files_hashed={s9_rows}")
    print(f"raw_bytes={s9_bytes}")
    print(f"supplementary_files_hashed={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
