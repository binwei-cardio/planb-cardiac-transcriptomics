# -*- coding: utf-8 -*-
"""Build visually checked PDFs for the Frontiers-style submission package."""
from pathlib import Path
from html import escape
import re
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from pypdf import PdfReader, PdfWriter
from PIL import Image as PILImage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_paths import PLANB_ROOT

ROOT = PLANB_ROOT
PKG = ROOT / "06_Manuscript" / "Frontiers_Submission_Package_20261118"
FIG = ROOT / "04_figures"
PDF = PKG / "PDFs"
PDF.mkdir(parents=True, exist_ok=True)
MD = ROOT / "06_Manuscript" / "PlanB_English_Manuscript_FrontCVM_v1_20261118.md"
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

for name, file in [
    ("TNR", "C:/Windows/Fonts/times.ttf"),
    ("TNR-Bold", "C:/Windows/Fonts/timesbd.ttf"),
    ("TNR-Italic", "C:/Windows/Fonts/timesi.ttf"),
    ("TNR-BoldItalic", "C:/Windows/Fonts/timesbi.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, file))

styles = getSampleStyleSheet()
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontName="TNR", fontSize=10.8, leading=15.2, alignment=TA_JUSTIFY, spaceAfter=6)
BODY_SMALL = ParagraphStyle("BodySmall", parent=BODY, fontSize=10.2, leading=13.2)
TITLE_STYLE = ParagraphStyle("TitleCustom", parent=styles["Title"], fontName="TNR-Bold", fontSize=17, leading=21, alignment=TA_LEFT, spaceAfter=14)
H1 = ParagraphStyle("H1Custom", parent=styles["Heading1"], fontName="TNR-Bold", fontSize=13, leading=16, spaceBefore=12, spaceAfter=6, keepWithNext=True)
H2 = ParagraphStyle("H2Custom", parent=styles["Heading2"], fontName="TNR-Bold", fontSize=11.5, leading=14, spaceBefore=9, spaceAfter=4, keepWithNext=True)
REF = ParagraphStyle("RefCustom", parent=BODY_SMALL, leftIndent=14, firstLineIndent=-14, spaceAfter=3)
CAPTION = ParagraphStyle("Caption", parent=BODY_SMALL, fontSize=9.5, leading=12, alignment=TA_JUSTIFY)


def clean_markup(text):
    text = text.replace("\\*", "*").replace("\\_", "_").replace("  ", " ")
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"\^([^\^]+?)\^", r"<super>\1</super>", text)
    return text


def para(text, style=BODY):
    return Paragraph(clean_markup(text), style)


def add_page_number(canvas, doc, header_text):
    canvas.saveState()
    canvas.setFont("TNR", 8)
    canvas.setFillColor(colors.HexColor("#5A6066"))
    canvas.drawRightString(A4[0] - 42, A4[1] - 26, header_text)
    canvas.drawCentredString(A4[0] / 2, 24, f"Page {doc.page}")
    canvas.restoreState()


def make_doc(path, title, header_text, story, include_header=True):
    doc = BaseDocTemplate(str(path), pagesize=A4, rightMargin=42, leftMargin=45, topMargin=58, bottomMargin=42, title=title[:240], author="Plan B authors" if include_header else "")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    def on_page(canvas, doc):
        if include_header:
            add_page_number(canvas, doc, header_text)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])
    doc.build(story)
    return path


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


def table_flowable(rows, table_kind):
    if not rows:
        return Spacer(1, 1)
    cols = max(len(r) for r in rows)
    data = []
    for row in rows:
        cells = [para(c if j < len(row) else "", CAPTION) for j, c in enumerate(row)]
        cells += [para("", CAPTION)] * (cols - len(row))
        data.append(cells)
    widths = [110, 60, 90, 115, 125] if table_kind == "table1" else [135, 125, 55, 50, 45, 90]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="CENTER")
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#A6A6A6")),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E7E6E6")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    return table


def add_markdown_story(story, anonymous=False):
    i = 0
    skip = False
    break_before = {"## References", "## Figure legends", "## Table 1. Datasets and evidence roles", "## Table 2. Summary of key results"}
    while i < len(LINES):
        raw = LINES[i].rstrip()
        s = raw.strip()
        if s in {"**Working manuscript v1**", "**Date: 18 November 2026**", "**Target journal: Frontiers in Cardiovascular Medicine**", "**Article type: Original Research**"}:
            i += 1; continue
        if anonymous and s == "## Authors and affiliations":
            skip = True; i += 1; continue
        if anonymous and s == "## Author contributions":
            skip = True; i += 1; continue
        if skip:
            if s.startswith("#"):
                skip = False
            else:
                i += 1; continue
        if s == "---":
            i += 1; continue
        if s.startswith("# "):
            story.append(Paragraph(clean_markup(s[2:].strip()), TITLE_STYLE)); i += 1; continue
        if s.startswith("## "):
            heading = s[3:].strip()
            if s in break_before:
                story.append(PageBreak())
            story.append(Paragraph(clean_markup(heading), H1)); i += 1; continue
        if s.startswith("### "):
            story.append(Paragraph(clean_markup(s[4:].strip()), H2)); i += 1; continue
        if not s:
            i += 1; continue
        if s.startswith("|"):
            table_lines = []
            while i < len(LINES) and LINES[i].strip().startswith("|"):
                table_lines.append(LINES[i].strip()); i += 1
            rows = parse_table(table_lines)
            header = " ".join(rows[0]) if rows else ""
            if "Tissue/modality" in header:
                continue
            if rows and rows[0][0] == "Dataset/comparison":
                story.append(table_flowable(TABLE2_ROWS, "table2")); story.append(Spacer(1, 8)); continue
            if rows and "Dataset" in rows[0][0] and "Species" in header:
                story.append(table_flowable(TABLE1_ROWS, "table1")); story.append(Spacer(1, 8)); continue
            story.append(table_flowable(rows, "table1")); story.append(Spacer(1, 8)); continue
        if s.startswith("- "):
            story.append(Paragraph(clean_markup(s[2:]), ParagraphStyle("Bullet", parent=BODY, leftIndent=12, firstLineIndent=-8, bulletIndent=2, spaceAfter=3), bulletText="-")); i += 1; continue
        if re.match(r"^\d+\.\s+", s):
            story.append(Paragraph(clean_markup(s), REF)); i += 1; continue
        parts = [s]; i += 1
        while i < len(LINES):
            nxt = LINES[i].strip()
            if not nxt or nxt.startswith("#") or nxt.startswith("|") or nxt.startswith("- ") or nxt == "---" or re.match(r"^\d+\.\s+", nxt):
                break
            parts.append(nxt); i += 1
        style = BODY_SMALL if s.startswith(("**Background:", "**Methods:", "**Results:", "**Conclusions:")) else BODY
        story.append(para(" ".join(parts), style))
    return story


def build_main(anonymous=False):
    story = add_markdown_story([], anonymous=anonymous)
    name = "Main_Manuscript_Anonymous.pdf" if anonymous else "Main_Manuscript_Identified.pdf"
    return make_doc(PDF / name, TITLE, "Frontiers in Cardiovascular Medicine | Original Research", story)


def build_title_page():
    items = [
        f"Journal: {JOURNAL}",
        f"Article type: {ARTICLE_TYPE}",
        "Title Page",
        TITLE,
        "Authors: Bin Wei, Jingjing Zeng, Ying Yang*",
        "Affiliation: Affiliated Hospital of Liaoning University of Traditional Chinese Medicine, No. 33 Beiling Street, Huanggu District, Shenyang, Liaoning Province, China",
        "Corresponding author: Ying Yang, yy20170225@sina.com",
        "Funding: Liaoning Provincial Department of Education, Grant No. LJKMZ20221343.",
        f"Word count: main text {MAIN_WORDS:,}; abstract {ABSTRACT_WORDS:,}. Figures: 5. Tables: 2. Supplementary material: Tables S1-S10, core result tables and code.",
    ]
    story = [Paragraph(clean_markup("Title Page"), TITLE_STYLE), Spacer(1, 10)]
    for item in items:
        story.append(para(item, H2 if item == "Title Page" else BODY))
    return make_doc(PDF / "Title_Page.pdf", "Title Page", "Title Page", story, include_header=False)


def build_cover_letter():
    lines = [
        "18 November 2026",
        "To the Editors,",
        f'We submit the manuscript entitled "{TITLE}" for consideration as an Original Research article in {JOURNAL}.',
        "This is a hypothesis-generating exploratory cross-dataset secondary analysis of seven public human and mouse single-cell, single-nucleus, and spatial transcriptomic datasets. Using a harmonised cell-type-resolved programme score, the study examined whether fibrotic, inflammatory, endothelial, metabolic, cardiomyocyte-stress, cytotoxic, and senescence programmes show directional recurrence across heart failure and cancer therapy-related cardiotoxicity. The integrated quantitative synthesis included approximately 499,147 cells or spatial spots.",
        "The main observation is that fibroblast Fibrosis-ECM and cytotoxic T-cell programmes were directionally higher in six of seven disease or cardiotoxicity contrasts. DoxCM and NICM overlapped substantially at the module level; no direct DoxCM-versus-NICM comparison survived FDR correction. Mouse ICI myocarditis Visium data showed spatial co-localisation but remain descriptive and directional because the design was 2-versus-2. The manuscript does not claim causality, a chemotherapy-exclusive signature, or TCM efficacy.",
        "We believe the work is relevant to the journal's cardiovascular medicine and cardio-oncology readership because it brings human heart failure, doxorubicin cardiomyopathy, immune checkpoint inhibitor myocarditis, and spatial tissue context into one explicitly exploratory framework. The manuscript includes a frozen results package, complete control-gene selections, raw-file SHA-256 records, and an archive member-level provenance audit.",
        "The authors declare no competing interests. The data sources and code package are described in the manuscript. A public code and data repository will be deposited before submission.",
        "Yours sincerely,",
        "Ying Yang, on behalf of all authors",
        "Ying Yang, yy20170225@sina.com",
    ]
    story = [Paragraph(clean_markup("Cover Letter"), TITLE_STYLE), Spacer(1, 10)]
    for line in lines:
        st = ParagraphStyle("Action", parent=BODY, textColor=colors.HexColor("#7A4E00")) if line.startswith("AUTHOR_INPUT_NEEDED") else BODY
        story.append(para(line, st))
    return make_doc(PDF / "Cover_Letter.pdf", "Cover Letter", "Cover Letter", story, include_header=False)


def build_highlights():
    bullets = [
        "Seven public human and mouse single-cell, single-nucleus, and spatial transcriptomic datasets were integrated in a hypothesis-generating exploratory secondary analysis.",
        "Fibroblast Fibrosis-ECM and cytotoxic T-cell programmes were directionally higher in six of seven disease or cardiotoxicity contrasts.",
        "DoxCM and NICM overlapped at the module level; no direct DoxCM-versus-NICM comparison survived FDR correction.",
        "Human HF and cardiomyopathy datasets provided independent directional and donor-limited sensitivity evidence.",
        "Mouse ICI Visium data described spatial co-localisation only, with no causal inference.",
        "The package includes frozen Table 2 values, complete control-gene selections, raw-file SHA-256 records, and archive member-level validation.",
    ]
    story = [Paragraph(clean_markup("Highlights"), TITLE_STYLE), Spacer(1, 10)]
    bstyle = ParagraphStyle("Bullet", parent=BODY, leftIndent=14, firstLineIndent=-9, bulletIndent=2)
    for item in bullets:
        story.append(Paragraph(clean_markup(item), bstyle, bulletText="-"))
    return make_doc(PDF / "Highlights.pdf", "Highlights", "Highlights", story, include_header=False)


def build_table_pdf(name, heading, table_lines, note, kind):
    rows = TABLE1_ROWS if kind == "table1" else TABLE2_ROWS
    story = [Paragraph(clean_markup(heading), TITLE_STYLE), Spacer(1, 8), table_flowable(rows, kind), Spacer(1, 8), para(note, CAPTION)]
    return make_doc(PDF / f"{name}.pdf", heading, heading, story, include_header=False)


def build_figure_atlas():
    story = [Paragraph(clean_markup("Figure Atlas"), TITLE_STYLE), para("Five main figures are provided as separate high-resolution files. The same legends appear in the manuscript.")]
    figures = [
        ("Figure 1", "PlanB_Figure1_StudyDesign_v2.png", "A, clinical convergence between HF and cancer therapy-related cardiotoxicity; B, dataset landscape and evidence tier; C, harmonised analysis pipeline; D, evidence hierarchy and claim boundary. The integrated quantitative synthesis includes approximately 499,147 cells or spatial spots."),
        ("Figure 2", "PlanB_Figure2_DoxCM_NICM_v2.png", "A-C, cell-type-by-programme Hedges' g heatmaps for DoxCM versus donor, NICM versus donor, and DoxCM versus NICM. D-F, sample-level module scores for fibroblast Fibrosis-ECM, cardiomyocyte senescence, and T/NK cytotoxic programmes. Direct DoxCM-versus-NICM contrasts did not survive FDR correction."),
        ("Figure 3", "PlanB_Figure3_HumanEvidence_v2.png", "A-C, cell-type-by-programme heatmaps for GSE288222 HF versus non-diseased, GSE298023 ICM versus donor, and GSE298023 DCM versus donor. D, focused biological-pair effect matrix. E, direction consistency across programme/contrast pairs."),
        ("Figure 4", "PlanB_Figure4_Spatial_v2.png", "A, tissue images with Fibrosis-ECM score overlays for two ICI and two IL-17A-neutralised sections. B-C, neighbourhood enrichment among fibrosis, inflammation, hypoxia, cardiomyocyte stress, and cytotoxic T-cell programmes. D, average Moran's I. The 2-versus-2 design is descriptive only and cannot support causal inference."),
        ("Figure 5", "PlanB_Figure5_CrossDataset_v2.png", "A, programme-by-contrast effect matrix. B, positive and negative direction counts. C, distribution of FDR-based evidence strength. The matrix is a directional synthesis, not a pooled effect-size meta-analysis."),
    ]
    for idx, (label, png, legend) in enumerate(figures, 1):
        story.append(PageBreak())
        story.append(Paragraph(clean_markup(label), H2))
        path = FIG / "png" / png
        with PILImage.open(path) as im:
            w, h = im.size
        max_w, max_h = 500, 560
        scale = min(max_w / w, max_h / h)
        story.append(Image(str(path), width=w * scale, height=h * scale))
        story.append(Spacer(1, 8))
        story.append(para(f"Figure {idx}. {legend}", CAPTION))
    return make_doc(PDF / "Figure_Atlas.pdf", "Figure Atlas", "Figure Atlas", story, include_header=False)


def merge_review():
    writer = PdfWriter()
    for name in ["Title_Page.pdf", "Main_Manuscript_Identified.pdf", "Figure_Atlas.pdf"]:
        reader = PdfReader(PDF / name)
        for page in reader.pages:
            writer.add_page(page)
    out = PDF / "Review_Package_with_Figures_Revised.pdf"
    with out.open("wb") as fh:
        writer.write(fh)
    return out


build_title_page()
build_cover_letter()
build_highlights()
build_main(False)
build_main(True)
build_table_pdf("Table_1_Datasets", "Table 1. Datasets and evidence roles", LINES[240:250], "Source: frozen Plan B dataset inventory. GSE298023 and GSE299032 sample-selection limitations are detailed in Supplementary Table S1.", "table1")
build_table_pdf("Table_2_Results", "Table 2. Summary of key results", LINES[252:261], "Frozen values. Do not edit without author approval.", "table2")
build_figure_atlas()
merge_review()
print("PDFs built", len(list(PDF.glob('*.pdf'))), PDF)
