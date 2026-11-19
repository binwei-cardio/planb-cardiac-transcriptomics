# -*- coding: utf-8 -*-
from pathlib import Path
import csv, hashlib, re, sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_paths import PLANB_ROOT

ROOT = PLANB_ROOT
ENG = ROOT / "06_Manuscript" / "PlanB_English_Manuscript_FrontCVM_v1_20261118.md"
CHN = ROOT / "06_Manuscript" / "PlanB_Chinese_Manuscript_v1_20261118.md"
SUP = ROOT / "06_Manuscript" / "Supplementary_corrected_v2_20261118"
SNAP = ROOT / "08_reports" / "PlanB_Supplementary_SHA256_snapshot_corrected_20261118.csv"
MANIFEST = SUP / "Supplementary_SHA256_manifest.csv"
OUT = ROOT / "08_reports" / "PlanB_PostAudit_Validation_20261118.md"
RAW = ROOT / "01_raw"
SCRIPTS = ROOT / "06_scripts"

checks = []


def check(name, ok, detail=""):
    detail = str(detail).replace("|", "/").replace("\n", " ")
    checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def refaudit(path: Path, heading: str):
    text = path.read_text(encoding="utf-8")
    body, refs = text.split(heading, 1)
    items = re.findall(r"(?m)^(\d+)\.\s+(.+)$", refs)[:40]
    nums = {int(n) for n, _ in items}
    cited = set()
    for token in re.findall(r"\[([0-9,\-]+)\]", body):
        for part in token.split(","):
            if "-" in part:
                a, b = map(int, part.split("-"))
                cited.update(range(a, b + 1))
            elif part.strip():
                cited.add(int(part))
    return len(items), sorted(nums - cited), sorted(cited - nums)


eng = ENG.read_text(encoding="utf-8")
chn = CHN.read_text(encoding="utf-8")
guide = (SUP / "Supplementary_Information_PlanB_v1.md").read_text(encoding="utf-8")

n1, u1, o1 = refaudit(ENG, "## References")
n2, u2, o2 = refaudit(CHN, "## 参考文献")
check("English references", n1 == 40 and not u1 and not o1, f"count={n1}, uncited={u1}, out_of_range={o1}")
check("Chinese references", n2 == 40 and not u2 and not o2, f"count={n2}, uncited={u2}, out_of_range={o2}")

en_nums = [
    "(+0.705; FDR = 0.0042)",
    "(+0.169; FDR = 0.0042)",
    "(+0.367; p = 0.071; FDR = 0.590)",
    "(+1.007; p = 0.077; FDR = 0.590)",
    "(+0.263; p = 0.036; FDR = 0.689)",
    "(+0.868; p = 0.036; FDR = 0.214)",
]
ch_nums = [
    "（差值+0.705；FDR=0.0042）",
    "（差值+0.169；FDR=0.0042）",
    "（+0.367；p=0.071；FDR=0.590）",
    "（+1.007；p=0.077；FDR=0.590）",
    "（+0.263；p=0.036；FDR=0.689）",
    "（+0.868；p=0.036；FDR=0.214）",
]
check("English Table 2 values in Results", all(x in eng for x in en_nums), [x for x in en_nums if x not in eng])
check("Chinese Table 2 values in Results", all(x in chn for x in ch_nums), [x for x in ch_nums if x not in chn])
check("English freeze label count", eng.lower().count("hypothesis-generating exploratory cross-dataset secondary analysis") >= 4, eng.lower().count("hypothesis-generating exploratory cross-dataset secondary analysis"))
check("Chinese freeze label count", chn.count("假设生成性、探索性跨数据集二次分析") >= 4, chn.count("假设生成性、探索性跨数据集二次分析"))
check("Mouse causal boundary", ("no causal inference" in eng.lower() or "cannot support causal inference" in eng.lower()) and ("不能推断因果关系" in chn or "不能支持因果推断" in chn))
check("DoxCM/NICM negative result", "No direct DoxCM-versus-NICM comparison survived FDR correction" in eng and "DoxCM与NICM的直接比较没有任何程序通过FDR校正" in chn)
check("TCM future-only boundary", "no efficacy inference is made" in eng.lower() and "不作任何疗效推断" in chn)

s1 = pd.read_csv(SUP / "Supplementary_Table_S1_Datasets.csv")
check("S1 GEO selection fields", all(c in s1.columns for c in ["GEO_GSM_total", "GSM_used", "Excluded_or_limitation", "Programmes_assessed", "Module_exceptions"]))
r298 = s1.loc[s1.Dataset == "GSE298023"].iloc[0]
r299 = s1.loc[s1.Dataset == "GSE299032"].iloc[0]
r292 = s1.loc[s1.Dataset == "GSE292067"].iloc[0]
r161 = s1.loc[s1.Dataset == "GSE161470"].iloc[0]
check("S1 critical sample-selection disclosures", int(r298.GEO_GSM_total) == 18 and int(r298.GSM_used) == 13 and "GSM9004762" in str(r298.Excluded_or_limitation) and int(r299.GEO_GSM_total) == 30 and int(r299.GSM_used) == 5 and "Nine GEO samples lacked raw files" in str(r292.Excluded_or_limitation) and "collapsed" in str(r161.Excluded_or_limitation), f"GSE298023={r298.GSM_used}/{r298.GEO_GSM_total}; GSE299032={r299.GSM_used}/{r299.GEO_GSM_total}")
check("GSE135805 S1 panel wording", "4,029-12,734" in str(s1.loc[s1.Dataset == "GSE135805", "Interpretation_boundary"].iloc[0]))

s4b = pd.read_csv(SUP / "Supplementary_Table_S4B_GSE135805_section_summary.csv")
m = dict(zip(s4b.GSM, s4b.Group))
check("GSE135805 corrected labels", m.get("GSM4030473") == "ICM" and m.get("GSM4030475") == "HCM", m)

s5 = pd.read_csv(SUP / "Supplementary_Table_S5_Alternative_scoring_tests.csv")
s5_counts = s5.groupby("Method").size().to_dict()
s5_modules = set(s5.Module)
primary = pd.read_csv(ROOT / "03_output" / "gse292067_celltype_permutation.csv")
merged = s5.merge(primary[["Comparison", "CellType", "Module", "diff"]], on=["Comparison", "CellType", "Module"], suffixes=("_alt", "_primary"))
concordance = {method: int((group.diff_alt.gt(0) == group.diff_primary.gt(0)).sum()) for method, group in merged.groupby("Method")}
s5_complete = len(s5) == 144 and s5_counts == {"Rank-based": 72, "Z-score": 72} and s5_modules == {"Fibrosis_ECM", "Tcell_cytotoxic", "CM_stress", "Senescence"} and concordance == {"Rank-based": 45, "Z-score": 45}
check("S5 completeness and concordance", s5_complete, f"rows={len(s5)}, counts={s5_counts}, concordance={concordance}")
check("S5 manuscript synchronization", "Supplementary Table S5" in eng and "45 of 72" in eng and "补充表S5" in chn and "45/72" in chn and "45/72" in guide)

s6 = pd.read_csv(SUP / "Supplementary_Table_S6_Senescence_sensitivity_tests.csv")
s6_counts = s6.groupby("Dataset").size().to_dict()
s6_inference = str(s6.loc[s6.Dataset == "GSE297745", "Inference"].iloc[0]).lower()
s6_ok = len(s6) == 13 and s6_counts.get("GSE298023") == 12 and s6_counts.get("GSE297745") == 1 and "no causal inference" in s6_inference
check("S6 supplemental Senescence completeness", s6_ok, f"rows={len(s6)}, counts={s6_counts}")
check("S6 manuscript synchronization", "Supplementary Table S6" in eng and "+0.020 (p = 1.0)" in eng and "补充表S6" in chn and "+0.020（p=1.0）" in chn and "S6" in guide)

s7 = pd.read_csv(SUP / "Supplementary_Table_S7_Seven_programme_cross_dataset_matrix.csv", index_col=0)
tier = pd.read_csv(SUP / "Supplementary_Table_S7_Seven_programme_cross_dataset_evidence_tier.csv", index_col=0)
s7_ok = s7.shape[0] == 7 and "Endothelial" in s7.index and s7.shape[1] == 7 and (tier.loc["Endothelial"] == "mixed/sensitivity").all()
check("S7 exploratory seven-programme matrix", s7_ok, f"shape={s7.shape}, modules={list(s7.index)}")
check("S7 manuscript synchronization", "Supplementary Table S7" in eng and "Endothelial effects were not directionally consistent" in eng and "补充表S7" in chn and "Endothelial方向不一致" in chn and "S7" in guide)

stale = ["not formally benchmarked", "Formal sensitivity outputs", "未进行正式敏感性", "未形成正式敏感性", "两种替代评分均未进入最终分析"]
stale_hits = [x for x in stale if x in eng or x in chn or x in guide]
check("Stale alternative-scoring statements removed", not stale_hits, stale_hits)

# S8: complete control-gene selection export.
s8_details = pd.read_csv(SUP / "Supplementary_Table_S8_Control_gene_selections.csv")
s8_summary = pd.read_csv(SUP / "Supplementary_Table_S8_Control_gene_summary.csv")
expected_units = {
    "GSE292067": 25,
    "GSE298023": 13,
    "GSE297745": 4,
    "GSE299032": 5,
    "GSE135805": 4,
    "GSE161470": 2,
    "GSE288222": 12,
}
actual_units = s8_summary.groupby("Dataset")["SampleID"].nunique().to_dict()
expected_summary_rows = {
    "GSE292067": 25 * 7,
    "GSE298023": 13 * 6,
    "GSE297745": 4 * 6,
    "GSE299032": 5 * 7,
    "GSE135805": 4 * 7,
    "GSE161470": 2 * 7,
    "GSE288222": 12 * 7,
}
actual_summary_rows = s8_summary.groupby("Dataset").size().to_dict()
dup = s8_details.duplicated(["Dataset", "SampleID", "Programme", "ControlGeneID"]).sum()
s8_ok = (
    set(actual_units) == set(expected_units)
    and actual_units == expected_units
    and actual_summary_rows == expected_summary_rows
    and len(s8_details) > 10000
    and dup == 0
    and s8_details["ControlGeneID"].notna().all()
)
check("S8 complete control-gene export", s8_ok, f"detail_rows={len(s8_details)}, units={actual_units}, summary_rows={actual_summary_rows}, duplicates={dup}")
check("S8 manuscript and guide synchronization", "Supplementary Table S8" in eng and "补充表S8" in chn and "S8" in guide)

# S9: every existing raw file is hashed and verified.
s9 = pd.read_csv(SUP / "Supplementary_Table_S9_Raw_file_SHA256.csv")
raw_files = sorted(p for p in RAW.rglob("*") if p.is_file())
raw_rels = {p.relative_to(RAW).as_posix() for p in raw_files}
s9_rels = set(s9.relative_path)
raw_mismatch = []
for row in s9.itertuples(index=False):
    p = RAW / row.relative_path
    if not p.exists() or p.stat().st_size != int(row.size_bytes):
        raw_mismatch.append(row.relative_path)
        continue
    if sha256(p) != row.sha256:
        raw_mismatch.append(row.relative_path)
raw_total = sum(p.stat().st_size for p in raw_files)
s9_ok = len(s9) == len(raw_files) and raw_rels == s9_rels and int(s9.size_bytes.sum()) == raw_total and not raw_mismatch
check("S9 complete raw-file SHA-256 inventory", s9_ok, f"rows={len(s9)}, actual_files={len(raw_files)}, bytes={raw_total}, mismatches={raw_mismatch}")
check("S9 manuscript and guide synchronization", "Supplementary Table S9" in eng and "补充表S9" in chn and "S9" in guide and "70" in guide)

# S10: canonical archive member validation and quarantine record.
s10 = pd.read_csv(SUP / "Supplementary_Table_S10_Raw_integrity_revalidation.csv")
s10_summary = pd.read_csv(SUP / "Supplementary_Table_S10_Raw_integrity_summary.csv")
canonical = s10[s10["artifact_scope"] == "canonical"]
quarantine = s10[s10["artifact_scope"] == "quarantine"]
canonical_archives = canonical[canonical["artifact_type"] == "raw_archive"]
quarantine_file = ROOT / str(quarantine["relative_path"].iloc[0]) if len(quarantine) else None
s10_members = int(pd.to_numeric(canonical["tar_member_count"], errors="coerce").fillna(0).sum())
quarantine_ok = (
    len(quarantine) == 1
    and int(pd.to_numeric(quarantine["tar_member_count"], errors="coerce").iloc[0]) == 8
    and quarantine_file is not None
    and quarantine_file.exists()
    and sha256(quarantine_file) == str(quarantine["local_sha256"].iloc[0])
)
s10_ok = (
    len(s10) == 14
    and len(canonical) == 13
    and s10_members == 240
    and canonical["size_match"].eq(True).all()
    and canonical["sha_match"].eq(True).all()
    and canonical_archives["official_member_set_match"].eq(True).all()
    and canonical_archives["official_member_size_match"].eq(True).all()
    and quarantine_ok
    and (s10_summary.loc[s10_summary.dataset == "GSE292067", "status"].iloc[0] == "PASS_WITH_QUARANTINED_DUPLICATE")
)
check("S10 official archive-member and quarantine validation", s10_ok, f"rows={len(s10)}, canonical={len(canonical)}, canonical_members={s10_members}, quarantine_members={int(pd.to_numeric(quarantine['tar_member_count'], errors='coerce').iloc[0]) if len(quarantine) else 'NA'}")
check("S10 manuscript, guide and hardening report synchronization", "Supplementary Table S10" in eng and "补充表S10" in chn and "S10" in guide and "GSE292067 canonical archive passed with 100 members" in guide and (ROOT / "08_reports" / "PlanB_Raw_Data_Hardening_20261118.md").exists())

# Path portability: no hard-coded drive paths and all scripts compile.
script_files = sorted(SCRIPTS.glob("*.py"))
rx_drive = re.compile(r"(?<![A-Za-z])[A-Z]:\\[A-Za-z0-9]")
drive_hits = []
compile_errors = []
for p in script_files:
    text = p.read_text(encoding="utf-8")
    if rx_drive.search(text):
        drive_hits.append(p.name)
    try:
        compile(text, str(p), "exec")
    except Exception as exc:
        compile_errors.append(f"{p.name}:{type(exc).__name__}:{exc}")
path_module = (SCRIPTS / "planb_paths.py").read_text(encoding="utf-8")
check("Path parameterization", not drive_hits and not compile_errors and "PLANB_ROOT" in path_module and "PLANB_PROJECT_ROOT" in path_module, f"scripts={len(script_files)}, drive_hits={drive_hits}, compile_errors={compile_errors}")
check("Portable-path manuscript and guide synchronization", "PLANB_ROOT" in eng and "PLANB_ROOT" in chn and "planb_paths.py" in guide)

manifest_rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
snapshot_rows = list(csv.DictReader(SNAP.open(encoding="utf-8")))
actual_files = {p.relative_to(SUP).as_posix() for p in SUP.rglob("*") if p.is_file() and p != MANIFEST}
manifest_files = {r["relative_path"] for r in manifest_rows}
check("Manifest file set complete", manifest_files == actual_files, f"manifest={len(manifest_files)}, actual={len(actual_files)}, missing={sorted(actual_files - manifest_files)[:10]}, extra={sorted(manifest_files - actual_files)[:10]}")
check("Manifest and corrected snapshot match", manifest_rows == snapshot_rows, f"manifest_rows={len(manifest_rows)}, snapshot_rows={len(snapshot_rows)}")

bad = []
for row in snapshot_rows:
    p = SUP / row["relative_path"]
    if not p.exists() or p.stat().st_size != int(row["size"]) or sha256(p) != row["sha256"]:
        bad.append(row["relative_path"])
check("Corrected Supplementary SHA snapshot", not bad, f"entries={len(snapshot_rows)}, mismatches={bad}")

remediation = (ROOT / "08_reports" / "PlanB_Supplementary_Audit_Remediation_20261118.md").read_text(encoding="utf-8")
readiness = (ROOT / "08_reports" / "PlanB_Submission_Readiness_20261118.md").read_text(encoding="utf-8")
check("Remediation report synchronized", "S8" in remediation and "S9" in remediation and "S10" in remediation and "70" in remediation and "hardcoded" not in remediation.lower())
check("Submission readiness synchronized", all(x in readiness for x in ["Table S8", "Table S9", "Table S10", "Supplementary_corrected_v2_20261118"]))

lines = [
    "# Plan B post-audit validation",
    "",
    f"- Checks: {len(checks)}",
    f"- PASS: {sum(c['status'] == 'PASS' for c in checks)}",
    f"- FAIL: {sum(c['status'] == 'FAIL' for c in checks)}",
    "",
    "| Check | Status | Detail |",
    "|---|---|---|",
]
for item in checks:
    lines.append(f"| {item['check']} | {item['status']} | {item['detail']} |")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print(f"checks={len(checks)} pass={sum(c['status'] == 'PASS' for c in checks)} fail={sum(c['status'] == 'FAIL' for c in checks)}")
for item in checks:
    if item["status"] == "FAIL":
        print("FAIL", item)
