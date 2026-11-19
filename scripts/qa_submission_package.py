# -*- coding: utf-8 -*-
from pathlib import Path
import re
import csv
import sys
import pdfplumber
from docx import Document
from pypdf import PdfReader
from PIL import Image

ROOT = Path(r"G:\Codex所有文件\ChatGPT\心脏肿瘤学\PlanB_Repro_v1")
PKG = ROOT / "06_Manuscript" / "Frontiers_Submission_Package_20261118"
PDF = PKG / "PDFs"
checks = []

def check(name, ok, detail=""):
    checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": str(detail)})

def pdf_text(name):
    with pdfplumber.open(PDF/name) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages), len(pdf.pages)

docx_files = sorted(PKG.glob("*.docx"))
pdf_files = sorted(p for p in PDF.glob("*.pdf") if p.name != "Review_Package_with_Figures.pdf")
check("DOCX deliverables", len(docx_files) == 9 and all(p.stat().st_size > 0 for p in docx_files), [p.name for p in docx_files])
check("PDF deliverables", len(pdf_files) == 9 and all(p.stat().st_size > 0 for p in pdf_files), [p.name for p in pdf_files])

for p in docx_files:
    try:
        d = Document(p)
        check(f"DOCX opens: {p.name}", True, f"paragraphs={len(d.paragraphs)}, tables={len(d.tables)}")
    except Exception as exc:
        check(f"DOCX opens: {p.name}", False, exc)

main_text, main_pages = pdf_text("Main_Manuscript_Identified.pdf")
anon_text, anon_pages = pdf_text("Main_Manuscript_Anonymous.pdf")
check("Main manuscript PDF", "1. Introduction" in main_text and "5. Conclusions" in main_text and "References" in main_text and "Figure legends" in main_text, f"pages={main_pages}")
check("Anonymous manuscript identity boundary", "Bin Wei" not in anon_text and "Ying Yang" not in anon_text and "Liaoning Provincial Department" not in anon_text, f"pages={anon_pages}")

for value in ["+0.705", "0.0042", "+0.169", "+0.367", "0.071", "0.590", "+1.007", "0.077", "+0.263", "0.036", "0.689", "+0.868", "0.214"]:
    check(f"Main PDF value {value}", value in main_text)
for phrase in ["no direct DoxCM-versus-NICM comparison survived FDR correction", "no causal inference", "no efficacy inference"]:
    check(f"Main PDF boundary: {phrase}", phrase.lower() in main_text.lower())

table1_text, table1_pages = pdf_text("Table_1_Datasets.pdf")
table2_text, table2_pages = pdf_text("Table_2_Results.pdf")
check("Table 2 header", "Dataset/comparison" in table2_text and "Cell type/programme" in table2_text and "p value" in table2_text and "FDR" in table2_text, f"pages={table2_pages}")
for value in ["+0.705", "+0.169", "+0.367", "+1.007", "+0.263", "+0.868"]:
    check(f"Table 2 value {value}", value in table2_text)

atlas_text, atlas_pages = pdf_text("Figure_Atlas.pdf")
with pdfplumber.open(PDF/"Figure_Atlas.pdf") as pdf:
    image_count = sum(len(page.images) for page in pdf.pages)
check("Figure Atlas", atlas_pages == 6 and image_count == 5, f"pages={atlas_pages}, images={image_count}")
check("Figure Atlas legends", all(f"Figure {i}." in atlas_text for i in range(1, 6)))

review_text, review_pages = pdf_text("Review_Package_with_Figures_Revised.pdf")
main_pages_int = len(PdfReader(str(PDF/"Main_Manuscript_Identified.pdf")).pages)
atlas_pages_int = len(PdfReader(str(PDF/"Figure_Atlas.pdf")).pages)
check("Review package composition", review_pages == main_pages_int + atlas_pages_int + 1, f"review={review_pages}, expected={1+main_pages_int+atlas_pages_int}")

with (PKG/"References_Numbered.csv").open(encoding="utf-8-sig") as fh:
    refs = list(csv.DictReader(fh))
check("Reference count", len(refs) == 40, len(refs))

with (PKG/"Main_Manuscript_Identified.docx").open("rb") as fh:
    d = Document(PKG/"Main_Manuscript_Identified.docx")
text_docx = "\n".join(p.text for p in d.paragraphs)
check("Data-availability duplicate removed", "Complete control-gene selections are provided in Supplementary Table S8, and the complete" not in text_docx)
main_flat = " ".join(main_text.split())
table1_flat = " ".join(table1_text.split())
table2_flat = " ".join(table2_text.split())
check("Table 1 and Table 2 explicit rows", "GSE292067 DoxCM vs donor" in main_flat and "GSE292067 DoxCM vs donor" in table2_flat and "GSE135805" in table1_flat and "Fibroblast/Fibrosis-ECM" in table2_flat)
title_text = "\n".join(p.text for p in Document(PKG/"Title_Page.docx").paragraphs)
cover_text = "\n".join(p.text for p in Document(PKG/"Cover_Letter.docx").paragraphs)
check("Submission-facing placeholders removed", "AUTHOR_INPUT_NEEDED" not in title_text and "AUTHOR_INPUT_NEEDED" not in cover_text and "[to be inserted]" not in text_docx and (PKG/"AUTHOR_METADATA_REQUEST.md").exists())

# Basic page-boundary check for all PDFs.
outside = []
for p in pdf_files:
    with pdfplumber.open(p) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            for word in page.extract_words():
                if word["x0"] < 0 or word["x1"] > page.width + 1 or word["top"] < 0 or word["bottom"] > page.height + 1:
                    outside.append(f"{p.name}:p{page_no}:{word['text']}")
check("PDF word boxes within page bounds", not outside, outside[:10])

with pdfplumber.open(PDF/"Main_Manuscript_Identified.pdf") as pdf:
    bad_cid = any("cid:" in (page.extract_text() or "") for page in pdf.pages)
check("PDF text extraction has no CID glyphs", not bad_cid)

# Figure assets copied.
figs = sorted((PKG/"Figures").glob("*"))
check("Figure asset count", len(figs) == 10, len(figs))
check("Figure TIFF resolution", all(Image.open(p).info.get("dpi", (0,0))[0] >= 300 for p in (PKG/"Figures").glob("*.tif")), "TIFF files checked")

lines = ["# Submission package QA", "", f"- Checks: {len(checks)}", f"- PASS: {sum(c['status']=='PASS' for c in checks)}", f"- FAIL: {sum(c['status']=='FAIL' for c in checks)}", "", "| Check | Status | Detail |", "|---|---|---|"]
for c in checks:
    lines.append(f"| {c['check']} | {c['status']} | {c['detail'].replace('|','/')} |")
out = PKG/"QA"/"Submission_Package_QA.md"
out.write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
print("QA checks", len(checks), "pass", sum(c['status']=='PASS' for c in checks), "fail", sum(c['status']=='FAIL' for c in checks))
for c in checks:
    if c['status']=='FAIL': print(c)
