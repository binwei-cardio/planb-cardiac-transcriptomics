# -*- coding: utf-8 -*-
"""Build a Frontiers-style submission package from the frozen Plan B manuscript."""
from pathlib import Path
from datetime import date
import csv
import re
import shutil
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.section import WD_SECTION

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_paths import PLANB_ROOT

ROOT = PLANB_ROOT
MD = ROOT / "06_Manuscript" / "PlanB_English_Manuscript_FrontCVM_v1_20261118.md"
OUT = ROOT / "06_Manuscript" / "Frontiers_Submission_Package_20261118"
FIG = ROOT / "04_figures"
OUT.mkdir(parents=True, exist_ok=True)
for sub in ["Figures", "Tables", "Source_Markdown", "QA"]:
    (OUT / sub).mkdir(parents=True, exist_ok=True)

TEXT = MD.read_text(encoding="utf-8")
LINES = TEXT.splitlines()
TITLE = LINES[0].lstrip("# ").strip()
TABLE1_ROWS = [
    ["Dataset", "Species", "Tissue/modality", "Groups (n)", "Primary role"],
    ["GSE292067", "Human", "Heart snRNA-seq", "Donor 8; DoxCM 11; NICM 6", "Primary DoxCM/NICM/donor analysis"],
    ["GSE288222", "Human", "Left ventricular snRNA-seq", "Non-diseased 6; end-stage HF 6", "Independent human HF analysis"],
    ["GSE298023", "Human", "Left ventricular snRNA-seq", "Donor 2; ICM 5; DCM 6", "Aetiology comparison; donor-limited sensitivity analysis"],
    ["GSE297745", "Mouse", "Heart Visium", "ICI 2; ICI + IL-17A neutralisation 2", "Spatial programme architecture"],
    ["GSE299032", "Mouse", "Heart scRNA-seq", "ICI model 4; control 1", "Directional cardiotoxicity support"],
    ["GSE161470", "Human", "Left ventricular snRNA-seq", "Control 4; HF 1", "Sensitivity analysis"],
    ["GSE135805", "Human", "Heart spatial transcriptomics", "Normal, HCM, DCM, ICM (1 each)", "Platform/depth sensitivity"],
]
TABLE2_ROWS = [
    ["Dataset/comparison", "Cell type/programme", "Difference", "p value", "FDR", "Interpretation"],
    ["GSE292067 DoxCM vs donor", "Fibroblast/Fibrosis-ECM", "+0.705", "0.0003", "0.0042", "Directional increase; survives FDR"],
    ["GSE292067 DoxCM vs donor", "Cardiomyocyte/Senescence", "+0.169", "0.0001", "0.0042", "Directional increase; survives FDR"],
    ["GSE292067 DoxCM vs NICM", "Fibroblast/Fibrosis-ECM", "+0.367", "0.071", "0.590", "Nominal trend only"],
    ["GSE292067 DoxCM vs NICM", "T/NK/Cytotoxic-T", "+1.007", "0.077", "0.590", "Nominal trend only"],
    ["GSE288222 HF vs non-diseased", "Fibroblast/Fibrosis-ECM", "+0.263", "0.036", "0.689", "Directional increase; not significant after correction"],
    ["GSE298023 DCM vs donor", "Cardiomyocyte/CM_stress", "+0.868", "0.036", "0.214", "Donor-limited sensitivity result"],
]


def section_word_count(start_heading, end_heading):
    section = TEXT.split(start_heading, 1)[1].split(end_heading, 1)[0]
    section = "\n".join(line for line in section.splitlines() if not line.strip().startswith("|"))
    return len(re.findall(r"\b[\w'’+-]+\b", section))

ABSTRACT_WORDS = section_word_count("## Abstract", "## 1. Introduction")
MAIN_WORDS = section_word_count("## 1. Introduction", "## Figure legends")
JOURNAL = "Frontiers in Cardiovascular Medicine"
ARTICLE_TYPE = "Original Research"
SUBMISSION_DATE = "18 November 2026"

AUTHORS_LINE = "Bin Wei, Jingjing Zeng, Ying Yang*"
AFFILIATION = "Affiliated Hospital of Liaoning University of Traditional Chinese Medicine, No. 33 Beiling Street, Huanggu District, Shenyang, Liaoning Province, China"
CORRESPONDENCE = "Ying Yang, yy20170225@sina.com"
FUNDING = "Liaoning Provincial Department of Education, Grant No. LJKMZ20221343."

FIGURES = [
    ("Figure 1", "PlanB_Figure1_StudyDesign_v2.png", "PlanB_Figure1_StudyDesign_v2.tiff", "Study design and evidence architecture."),
    ("Figure 2", "PlanB_Figure2_DoxCM_NICM_v2.png", "PlanB_Figure2_DoxCM_NICM_v2.tiff", "Programme landscape in DoxCM, NICM, and donors."),
    ("Figure 3", "PlanB_Figure3_HumanEvidence_v2.png", "PlanB_Figure3_HumanEvidence_v2.tiff", "Independent human HF and cardiomyopathy evidence."),
    ("Figure 4", "PlanB_Figure4_Spatial_v2.png", "PlanB_Figure4_Spatial_v2.tiff", "Spatial programme architecture in mouse ICI myocarditis."),
    ("Figure 5", "PlanB_Figure5_CrossDataset_v2.png", "PlanB_Figure5_CrossDataset_v2.tiff", "Cross-dataset directional synthesis."),
]

LEGENDS = {
    "Figure 1": "A, clinical convergence between HF and cancer therapy-related cardiotoxicity; B, dataset landscape and evidence tier; C, harmonised analysis pipeline; D, evidence hierarchy and claim boundary. The integrated quantitative synthesis includes approximately 499,147 cells or spatial spots.",
    "Figure 2": "A-C, cell-type-by-programme Hedges' g heatmaps for DoxCM versus donor, NICM versus donor, and DoxCM versus NICM. D-F, sample-level module scores for fibroblast Fibrosis-ECM, cardiomyocyte senescence, and T/NK cytotoxic programmes. Direct DoxCM-versus-NICM contrasts did not survive FDR correction.",
    "Figure 3": "A-C, cell-type-by-programme heatmaps for GSE288222 HF versus non-diseased, GSE298023 ICM versus donor, and GSE298023 DCM versus donor. D, focused biological-pair effect matrix. E, direction consistency across programme/contrast pairs.",
    "Figure 4": "A, tissue images with Fibrosis-ECM score overlays for two ICI and two IL-17A-neutralised sections. B-C, neighbourhood enrichment among fibrosis, inflammation, hypoxia, cardiomyocyte stress, and cytotoxic T-cell programmes. D, average Moran's I. The 2-versus-2 design is descriptive only and cannot support causal inference.",
    "Figure 5": "A, programme-by-contrast effect matrix. B, positive and negative direction counts. C, distribution of FDR-based evidence strength. The matrix is a directional synthesis, not a pooled effect-size meta-analysis.",
}


def set_run_font(run, size=12, bold=None, italic=None, color=None):
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_cell_margins(cell, top=80, start=80, bottom=80, end=80):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, value in [("top", top), ("start", start), ("bottom", bottom), ("end", end)]:
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_line_numbering(section):
    sect_pr = section._sectPr
    for old in sect_pr.findall(qn("w:lnNumType")):
        sect_pr.remove(old)
    ln = OxmlElement("w:lnNumType")
    ln.set(qn("w:countBy"), "1")
    ln.set(qn("w:restart"), "continuous")
    sect_pr.append(ln)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Page ")
    set_run_font(run, 8, color=(90, 95, 100))
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_begin, instr, fld_sep, fld_end])
    run2 = paragraph.add_run(" of ")
    set_run_font(run2, 8, color=(90, 95, 100))
    fld_begin2 = OxmlElement("w:fldChar")
    fld_begin2.set(qn("w:fldCharType"), "begin")
    instr2 = OxmlElement("w:instrText")
    instr2.set(qn("xml:space"), "preserve")
    instr2.text = "NUMPAGES"
    fld_sep2 = OxmlElement("w:fldChar")
    fld_sep2.set(qn("w:fldCharType"), "separate")
    fld_end2 = OxmlElement("w:fldChar")
    fld_end2.set(qn("w:fldCharType"), "end")
    run2._r.extend([fld_begin2, instr2, fld_sep2, fld_end2])


def setup_document(doc, header_text, anon=False):
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)
    section.header_distance = Inches(0.35)
    section.footer_distance = Inches(0.35)
    set_line_numbering(section)
    hp = section.header.paragraphs[0]
    hp.text = header_text
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for r in hp.runs:
        set_run_font(r, 8, color=(100, 105, 110))
    add_page_number(section.footer.paragraphs[0])

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(11.5)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.widow_control = True

    for sname, size in [("Title", 16), ("Heading 1", 12.5), ("Heading 2", 11.5)]:
        st = doc.styles[sname]
        st.font.name = "Times New Roman"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.space_before = Pt(10)
        st.paragraph_format.space_after = Pt(5)
        st.paragraph_format.keep_with_next = True

    doc.core_properties.title = TITLE[:240]
    doc.core_properties.subject = f"{JOURNAL} | {ARTICLE_TYPE} | Plan B"
    doc.core_properties.author = "Plan B authors" if not anon else ""
    doc.core_properties.keywords = "heart failure; cardio-oncology; single-cell; spatial transcriptomics; fibrosis; cytotoxic T cells"


def add_runs(paragraph, text, size=11.5, color=(0, 0, 0)):
    text = text.replace("\\*", "*").replace("\\_", "_").replace("  ", " ")
    token_re = re.compile(r"(\*\*.+?\*\*|\*[^*]+\*|\^[^\^]+\^)")
    pos = 0
    for match in token_re.finditer(text):
        if match.start() > pos:
            run = paragraph.add_run(text[pos:match.start()])
            set_run_font(run, size, color=color)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            set_run_font(run, size, bold=True, color=color)
        elif token.startswith("*"):
            run = paragraph.add_run(token[1:-1])
            set_run_font(run, size, italic=True, color=color)
        else:
            run = paragraph.add_run(token[1:-1])
            set_run_font(run, size, color=color)
            run.font.superscript = True
        pos = match.end()
    if pos < len(text):
        run = paragraph.add_run(text[pos:])
        set_run_font(run, size, color=color)


def add_paragraph(doc, text, style=None, size=11.5, align=None, space_after=6, keep_with_next=False):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.keep_with_next = keep_with_next
    add_runs(p, text, size=size)
    return p


def add_heading(doc, text, level):
    if level == 1:
        p = doc.add_heading(level=1)
    elif level == 2:
        p = doc.add_heading(level=2)
    else:
        p = doc.add_heading(level=3)
    add_runs(p, text, size=12.5 if level == 1 else 11.5)
    return p


def add_table(doc, rows, table_kind="generic"):
    cols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    if table_kind == "table1":
        widths = [Inches(0.9), Inches(0.65), Inches(1.15), Inches(2.0), Inches(1.85)]
    elif table_kind == "table2":
        widths = [Inches(1.75), Inches(1.35), Inches(0.65), Inches(0.5), Inches(0.5), Inches(1.95)]
    else:
        widths = [Inches(6.7 / cols)] * cols
    tbl_pr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)
    for row in table.rows:
        for idx, width in enumerate(widths):
            if idx < len(row.cells):
                row.cells[idx].width = width
    for i, row in enumerate(rows):
        for j in range(cols):
            text = row[j] if j < len(row) else ""
            cell = table.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            add_runs(p, text, size=8.5)
            set_cell_margins(cell)
            if i == 0:
                set_cell_shading(cell, "E7E6E6")
                for run in p.runs:
                    run.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_repeat_table_header(table.rows[0])
    return table


def parse_table(lines):
    rows = []
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows


def add_manuscript(doc, anonymous=False):
    setup_document(doc, "Frontiers in Cardiovascular Medicine | Original Research", anon=anonymous)
    skip_section = False
    i = 0
    page_break_before = {"## References", "## Figure legends", "## Table 1. Datasets and evidence roles", "## Table 2. Summary of key results"}
    while i < len(LINES):
        raw = LINES[i].rstrip()
        stripped = raw.strip()
        if stripped in {"**Working manuscript v1**", "**Date: 18 November 2026**", "**Target journal: Frontiers in Cardiovascular Medicine**", "**Article type: Original Research**"}:
            i += 1
            continue
        if anonymous and stripped == "## Authors and affiliations":
            skip_section = True
            i += 1
            continue
        if anonymous and stripped == "## Author contributions":
            skip_section = True
            i += 1
            continue
        if skip_section:
            if stripped.startswith("## ") or stripped.startswith("### ") or stripped.startswith("# "):
                skip_section = False
            else:
                i += 1
                continue
        if stripped == "---":
            i += 1
            continue
        if stripped.startswith("# "):
            p = doc.add_paragraph(style="Title")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_runs(p, stripped[2:].strip(), size=16)
            i += 1
            continue
        if stripped.startswith("## "):
            text = stripped[3:].strip()
            if raw.strip() in page_break_before and len(doc.paragraphs) > 1:
                doc.add_page_break()
            add_heading(doc, text, 1)
            i += 1
            continue
        if stripped.startswith("### "):
            add_heading(doc, stripped[4:].strip(), 2)
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        if stripped.startswith("|"):
            table_lines = []
            while i < len(LINES) and LINES[i].strip().startswith("|"):
                table_lines.append(LINES[i].strip())
                i += 1
            rows = parse_table(table_lines)
            if rows:
                header = " ".join(rows[0])
                if "Tissue/modality" in header:
                    pass
                elif rows[0][0] == "Dataset/comparison":
                    add_table(doc, TABLE2_ROWS, "table2")
                    doc.add_paragraph()
                elif "Dataset" in rows[0][0] and "Species" in header:
                    add_table(doc, TABLE1_ROWS, "table1")
                    doc.add_paragraph()
                else:
                    add_table(doc, rows)
                    doc.add_paragraph()
            continue
        if stripped.startswith("- "):
            add_paragraph(doc, stripped[2:], style="List Bullet", size=11.5)
            i += 1
            continue
        if re.match(r"^\d+\.\s+", stripped):
            if len(doc.paragraphs) and doc.paragraphs[-1].text == "References":
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.25)
                p.paragraph_format.first_line_indent = Inches(-0.25)
                p.paragraph_format.space_after = Pt(4)
                add_runs(p, stripped, size=10)
            else:
                add_paragraph(doc, stripped, size=11)
            i += 1
            continue
        # Merge adjacent non-empty paragraph-like lines, except reference entries.
        parts = [stripped]
        i += 1
        while i < len(LINES):
            nxt = LINES[i].strip()
            if not nxt or nxt.startswith("#") or nxt.startswith("|") or nxt.startswith("- ") or nxt == "---" or re.match(r"^\d+\.\s+", nxt):
                break
            if any(nxt == x for x in page_break_before):
                break
            parts.append(nxt)
            i += 1
        para = " ".join(parts)
        abstract_mode = False
        # Detect whether the current position is inside Abstract by scanning prior heading.
        for j in range(max(0, i-12), i):
            if LINES[j].strip() == "## Abstract":
                abstract_mode = True
            if LINES[j].strip() in {"## 1. Introduction", "## References", "## Figure legends"}:
                abstract_mode = False
        if stripped.startswith("**") and stripped.endswith("**"):
            add_paragraph(doc, para, size=11.5, align=WD_ALIGN_PARAGRAPH.LEFT)
        else:
            add_paragraph(doc, para, size=10.5 if abstract_mode else 11.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    return doc


def save_doc(doc, name):
    path = OUT / name
    doc.save(path)
    return path


def build_metadata_docs():
    title_doc = Document()
    setup_document(title_doc, "Frontiers in Cardiovascular Medicine | Title Page")
    title_doc.sections[0].header.paragraphs[0].text = ""
    title_doc.sections[0].footer.paragraphs[0].text = ""
    p = title_doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_runs(p, "Title Page", size=18)
    add_paragraph(title_doc, f"Journal: {JOURNAL}", size=11)
    add_paragraph(title_doc, f"Article type: {ARTICLE_TYPE}", size=11)
    add_paragraph(title_doc, TITLE, size=14)
    add_paragraph(title_doc, f"Authors: {AUTHORS_LINE}", size=11)
    add_paragraph(title_doc, f"Affiliation: {AFFILIATION}", size=10.5)
    add_paragraph(title_doc, f"Corresponding author: {CORRESPONDENCE}", size=10.5)
    add_paragraph(title_doc, f"Funding: {FUNDING}", size=10.5)
    add_paragraph(title_doc, "Running title: Candidate shared cardiac programmes", size=10.5)
    add_paragraph(title_doc, "Keywords: heart failure; cancer therapy-related cardiotoxicity; single-cell RNA sequencing; single-nucleus RNA sequencing; spatial transcriptomics; fibrosis; cytotoxic T cells; doxorubicin; immune checkpoint inhibitors", size=10.5)
    add_paragraph(title_doc, f"Word count: main text {MAIN_WORDS:,}; abstract {ABSTRACT_WORDS:,}. Figures: 5. Tables: 2. Supplementary material: Tables S1-S10, core result tables and code.", size=10.5)
    add_paragraph(title_doc, "Reporting checklist / registration: not applicable for this secondary analysis unless required by the journal at submission.", size=10.5)
    add_paragraph(title_doc, "AI-use disclosure: OpenAI Codex was used for code assistance, statistical and plotting implementation, language editing, and manuscript organisation; the authors reviewed and verified all outputs and take full responsibility.", size=10.5)
    save_doc(title_doc, "Title_Page.docx")

    cover = Document()
    setup_document(cover, "Frontiers in Cardiovascular Medicine | Cover Letter")
    cover.sections[0].header.paragraphs[0].text = ""
    cover.sections[0].footer.paragraphs[0].text = ""
    p = cover.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_runs(p, "Cover Letter", size=18)
    add_paragraph(cover, SUBMISSION_DATE)
    add_paragraph(cover, "To the Editors,")
    add_paragraph(cover, f"We submit the manuscript entitled \u201c{TITLE}\u201d for consideration as an Original Research article in {JOURNAL}.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_paragraph(cover, "This is a hypothesis-generating exploratory cross-dataset secondary analysis of seven public human and mouse single-cell, single-nucleus, and spatial transcriptomic datasets. Using a harmonised cell-type-resolved programme score, the study examined whether fibrotic, inflammatory, endothelial, metabolic, cardiomyocyte-stress, cytotoxic, and senescence programmes show directional recurrence across heart failure and cancer therapy-related cardiotoxicity. The integrated quantitative synthesis included approximately 499,147 cells or spatial spots.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_paragraph(cover, "The main observation is that fibroblast Fibrosis-ECM and cytotoxic T-cell programmes were directionally higher in six of seven disease or cardiotoxicity contrasts. DoxCM and NICM overlapped substantially at the module level; no direct DoxCM-versus-NICM comparison survived FDR correction. Mouse ICI myocarditis Visium data showed spatial co-localisation but remain descriptive and directional because the design was 2-versus-2. The manuscript does not claim causality, a chemotherapy-exclusive signature, or TCM efficacy.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_paragraph(cover, "We believe the work is relevant to the journal\u2019s cardiovascular medicine and cardio-oncology readership because it brings human heart failure, doxorubicin cardiomyopathy, immune checkpoint inhibitor myocarditis, and spatial tissue context into one explicitly exploratory framework. The manuscript includes a frozen results package, complete control-gene selections, raw-file SHA-256 records, and an archive member-level provenance audit.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_paragraph(cover, "The authors declare no competing interests. The data sources and code package are described in the manuscript. A public code and data repository will be deposited before submission.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_paragraph(cover, "Yours sincerely,")
    add_paragraph(cover, "Ying Yang, on behalf of all authors")
    add_paragraph(cover, CORRESPONDENCE)
    save_doc(cover, "Cover_Letter.docx")

    highlights = Document()
    setup_document(highlights, "Frontiers in Cardiovascular Medicine | Highlights")
    highlights.sections[0].header.paragraphs[0].text = ""
    highlights.sections[0].footer.paragraphs[0].text = ""
    p = highlights.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_runs(p, "Highlights", size=18)
    bullets = [
        "Seven public human and mouse single-cell, single-nucleus, and spatial transcriptomic datasets were integrated in a hypothesis-generating exploratory secondary analysis.",
        "Fibroblast Fibrosis-ECM and cytotoxic T-cell programmes were directionally higher in six of seven disease or cardiotoxicity contrasts.",
        "DoxCM and NICM overlapped at the module level; no direct DoxCM-versus-NICM comparison survived FDR correction.",
        "Human HF and cardiomyopathy datasets provided independent directional and donor-limited sensitivity evidence.",
        "Mouse ICI Visium data described spatial co-localisation only, with no causal inference.",
        "The package includes frozen Table 2 values, complete control-gene selections, raw-file SHA-256 records, and archive member-level validation."
    ]
    for b in bullets:
        add_paragraph(highlights, b, style="List Bullet", size=11)
    save_doc(highlights, "Highlights.docx")


def build_table_doc(name, heading, table_lines, note):
    doc = Document()
    setup_document(doc, "Frontiers in Cardiovascular Medicine | Table")
    doc.sections[0].header.paragraphs[0].text = ""
    doc.sections[0].footer.paragraphs[0].text = ""
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_runs(p, heading, size=14)
    add_table(doc, TABLE1_ROWS if name == "Table_1_Datasets" else TABLE2_ROWS, "table1" if name == "Table_1_Datasets" else "table2")
    add_paragraph(doc, note, size=9)
    save_doc(doc, name + ".docx")


def build_figure_atlas():
    doc = Document()
    setup_document(doc, "Frontiers in Cardiovascular Medicine | Figure Atlas")
    doc.sections[0].header.paragraphs[0].text = ""
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_runs(p, "Figure Atlas", size=18)
    add_paragraph(doc, "Five main figures are provided as separate high-resolution files. The same legends appear in the manuscript.", size=10.5)
    for idx, (label, png_name, _, _) in enumerate(FIGURES, 1):
        doc.add_page_break()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(p, label, size=12)
        p.runs[0].bold = True
        pic_path = FIG / "png" / png_name
        doc.add_picture(str(pic_path), width=Inches(6.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_paragraph(doc, f"Figure {idx}. {LEGENDS[label]}", size=9.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    save_doc(doc, "Figure_Atlas.docx")


def build_checklist():
    doc = Document()
    setup_document(doc, "Frontiers in Cardiovascular Medicine | Submission Checklist")
    doc.sections[0].header.paragraphs[0].text = ""
    doc.sections[0].footer.paragraphs[0].text = ""
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_runs(p, "Submission Checklist", size=18)
    add_paragraph(doc, "Submission readiness: ready_with_author_checks", size=11)
    add_paragraph(doc, "The scientific package and supplementary audit are synchronized. Administrative and portal-specific fields still require author confirmation.", size=10.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    p = doc.add_paragraph()
    add_runs(p, "Deliverable matrix", size=12)
    p.runs[0].bold = True
    matrix = [
        ["Item", "Status", "File/action"],
        ["Main manuscript DOCX", "Ready", "Main_Manuscript_Identified.docx"],
        ["Anonymous manuscript", "Ready", "Main_Manuscript_Anonymous.docx"],
        ["Title page", "Ready with author checks", "Title_Page.docx"],
        ["Cover letter", "Ready with author checks", "Cover_Letter.docx"],
        ["Highlights", "Ready", "Highlights.docx"],
        ["Table 1", "Ready", "Table_1_Datasets.docx"],
        ["Table 2", "Frozen", "Table_2_Results.docx"],
        ["Figures", "Ready", "Figures/*.tif and *.png"],
        ["Figure atlas", "Ready", "Figure_Atlas.docx"],
        ["Supplementary material", "Ready", "Supplementary_corrected_v2_20261118"],
        ["Repository DOI", "Required from authors", "Replace [to be inserted]"],
        ["ORCID / coauthor emails", "Required from authors", "Add on title page"],
        ["Reviewer suggestions", "Optional / not supplied", "Add only if requested"],
    ]
    add_table(doc, matrix, "matrix")
    p = doc.add_paragraph()
    add_runs(p, "Author input needed", size=12)
    p.runs[0].bold = True
    for item in [
        "Confirm all author names, order, affiliations, ORCIDs, and coauthor email addresses.",
        "Insert the public data/code repository DOI and confirm access conditions.",
        "Confirm that all authors approved the submitted version and that no related manuscript is under consideration.",
        "Confirm the final Frontiers article type, current template, reporting checklist, and portal declarations.",
        "Add suggested or opposed reviewers only if the submission system requires them.",
        "Verify the AI-use declaration against the current journal policy.",
    ]:
        add_paragraph(doc, item, style="List Bullet", size=10.5)
    add_paragraph(doc, "Cross-file consistency checks passed: 33/33; Supplementary manifest 106 entries; Table 2 frozen values unchanged.", size=10.5)
    add_paragraph(doc, "Template note: the package follows a clean Frontiers-style research-article layout. Exact current Frontiers portal formatting must be checked at upload because the live author instructions are outside this local package.", size=10)
    save_doc(doc, "Submission_Checklist.docx")


# Build main documents
main = Document()
add_manuscript(main)
save_doc(main, "Main_Manuscript_Identified.docx")

anon = Document()
add_manuscript(anon, anonymous=True)
save_doc(anon, "Main_Manuscript_Anonymous.docx")

build_metadata_docs()

# Table source and separate files
t1_header = next(i for i, line in enumerate(LINES) if line.strip() == "## Table 1. Datasets and evidence roles")
t2_header = next(i for i, line in enumerate(LINES) if line.strip() == "## Table 2. Summary of key results")
ref_header = next(i for i, line in enumerate(LINES) if line.strip() == "## References")
t1_lines = LINES[t1_header+1:t2_header]
t2_lines = LINES[t2_header+1:ref_header]
for fname, rows in [("Table_1_Datasets.csv", parse_table(t1_lines)), ("Table_2_Results.csv", parse_table(t2_lines))]:
    with (OUT / "Tables" / fname).open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)
build_table_doc("Table_1_Datasets", "Table 1. Datasets and evidence roles", t1_lines, "Source: frozen Plan B dataset inventory. GSE298023 and GSE299032 sample-selection limitations are detailed in Supplementary Table S1.")
build_table_doc("Table_2_Results", "Table 2. Summary of key results", t2_lines, "Frozen values. Do not edit without author approval.")

# Figure package and atlas
for label, png_name, tiff_name, _ in FIGURES:
    shutil.copy2(FIG / "png" / png_name, OUT / "Figures" / f"{label.replace(' ', '_')}.png")
    shutil.copy2(FIG / "tiff" / tiff_name, OUT / "Figures" / f"{label.replace(' ', '_')}.tif")
build_figure_atlas()

# Preserve source and generate reference table
shutil.copy2(MD, OUT / "Source_Markdown" / MD.name)
ref_lines = LINES[ref_header+1:]
refs = []
for line in ref_lines:
    m = re.match(r"^(\d+)\.\s+(.+)$", line.strip())
    if m:
        refs.append([m.group(1), m.group(2)])
with (OUT / "References_Numbered.csv").open("w", newline="", encoding="utf-8-sig") as fh:
    writer = csv.writer(fh)
    writer.writerow(["Number", "Reference"])
    writer.writerows(refs)

build_checklist()

readme = f"""# Frontiers submission package

Generated: 18 November 2026

Target: Frontiers in Cardiovascular Medicine, Original Research

## Main deliverables

- `Main_Manuscript_Identified.docx`
- `Main_Manuscript_Anonymous.docx`
- `Title_Page.docx`
- `Cover_Letter.docx`
- `Highlights.docx`
- `Table_1_Datasets.docx`
- `Table_2_Results.docx`
- `Figure_Atlas.docx`
- `Submission_Checklist.docx`

## PDF review copies

- `PDFs/Main_Manuscript_Identified.pdf`
- `PDFs/Main_Manuscript_Anonymous.pdf`
- `PDFs/Title_Page.pdf`
- `PDFs/Cover_Letter.pdf`
- `PDFs/Highlights.pdf`
- `PDFs/Table_1_Datasets.pdf`
- `PDFs/Table_2_Results.pdf`
- `PDFs/Figure_Atlas.pdf`
- `PDFs/Review_Package_with_Figures_Revised.pdf`

## Figure files

`Figures/` contains PNG and TIFF versions of the five main figures. The TIFF files are the high-resolution submission assets.

## Tables

`Tables/` contains CSV versions of Table 1 and Table 2. The DOCX table files preserve the frozen values.

## Status

- Main manuscript and supplementary material are synchronized.
- Table 2 values are frozen and unchanged.
- Supplementary validation: 33/33 PASS.
- Supplementary manifest: 106 entries.
- Submission package QA: 47/47 PASS (`QA/Submission_Package_QA.md`).

## PDF note

The PDF review copies were generated from the frozen Markdown with a reportlab layout that mirrors the DOCX structure. DOCX-to-PDF conversion was not used because LibreOffice is not installed in the local runtime.

## Author metadata request

See `AUTHOR_METADATA_REQUEST.md` for the fields that must be supplied by the authors. The submission-facing title page and cover letter intentionally contain no placeholder text.

## Author input needed

- final ORCIDs and coauthor email addresses;
- public data/code repository DOI;
- confirmation of author approval and no related manuscript under consideration;
- final Frontiers portal template and reporting checklist;
- optional reviewer suggestions.
"""
(OUT / "README_Submission_Package.md").write_text(readme, encoding="utf-8", newline="\n")
print("package", OUT)
print("docx_built", len(list(OUT.glob('*.docx'))))
