# -*- coding: utf-8 -*-
"""Reformat the English manuscript references into consistent Frontiers/Vancouver style."""
from pathlib import Path
import csv
import re

ROOT = Path(r"G:\Codex所有文件\ChatGPT\心脏肿瘤学\PlanB_Repro_v1")
MD = ROOT / "06_Manuscript" / "PlanB_English_Manuscript_FrontCVM_v1_20261118.md"
PKG = ROOT / "06_Manuscript" / "Frontiers_Submission_Package_20261118"
BACKUP = PKG / "References_Numbered.csv"
OUTCSV = PKG / "References_Vancouver.csv"
AUDIT = ROOT / "08_reports" / "PlanB_Reference_Format_Audit_20261118.md"

text = MD.read_text(encoding="utf-8")
head, refs_part = text.split("## References", 1)

# Use the pre-formatting reference extract as the lossless source when available.
refs = []
if BACKUP.exists():
    with BACKUP.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            refs.append((int(row["Number"]), row["Reference"].strip()))
if len(refs) != 40:
    for line in refs_part.splitlines():
        m = re.match(r"^(\d+)\.\s+(.+)$", line.strip())
        if m:
            refs.append((int(m.group(1)), m.group(2).strip()))
if len(refs) != 40:
    raise RuntimeError(f"Expected 40 source references, got {len(refs)}")

journal_abbrev = {
    "Nature Reviews Cardiology": "Nat Rev Cardiol",
    "Lancet": "Lancet",
    "Frontiers in Cardiovascular Medicine": "Front Cardiovasc Med",
    "Journal of Clinical Investigation": "J Clin Invest",
    "Nature Reviews Cancer": "Nat Rev Cancer",
    "Nature Communications": "Nat Commun",
    "Nature Cardiovascular Research": "Nat Cardiovasc Res",
    "Cardiovascular Research": "Cardiovasc Res",
    "Nature": "Nature",
    "Seminars in Cell & Developmental Biology": "Semin Cell Dev Biol",
    "Basic Research in Cardiology": "Basic Res Cardiol",
    "American Journal of Physiology-Cell Physiology": "Am J Physiol Cell Physiol",
    "Cell": "Cell",
    "Circulation": "Circulation",
    "Genome Medicine": "Genome Med",
    "Scientific Reports": "Sci Rep",
    "Journal of the American College of Cardiology": "J Am Coll Cardiol",
    "Frontiers in Pharmacology": "Front Pharmacol",
    "Biomedicine & Pharmacotherapy": "Biomed Pharmacother",
    "Cells": "Cells",
    "Phytomedicine": "Phytomedicine",
    "Journal of Inflammation Research": "J Inflamm Res",
    "JAMA Oncology": "JAMA Oncol",
    "Nucleic Acids Research": "Nucleic Acids Res",
    "European Heart Journal": "Eur Heart J",
    "Briefings in Bioinformatics": "Brief Bioinform",
    "Journal of Translational Medicine": "J Transl Med",
    "Journal of Cancer": "J Cancer",
    "Journal of Xenobiotics": "J Xenobiot",
}

formatted = []
audit = []
for num, ref in refs:
    gse = re.match(
        r"^Gene Expression Omnibus\.\s+(GSE\d+):\s+(.+?)\.\s+NCBI GEO\.\s+Accession:\s+(GSE\d+)\.$",
        ref,
    )
    if gse:
        acc = gse.group(1)
        title = gse.group(2).rstrip(".")
        formatted.append(
            f"{num}. NCBI Gene Expression Omnibus. {acc}: {title} [Data set]. "
            f"NCBI GEO; accessed 2026 Nov 18. Available from: "
            f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={acc}"
        )
        audit.append({"number": num, "type": "GEO", "journal": "NCBI GEO", "doi": "", "pmid": "", "status": "database_citation"})
        continue

    m = re.match(r"^(.+?)\.\s+(.+?)\.\s+\*(.+?)\*\.\s+(\d{4});(.+?)\.\s*(.*)$", ref)
    if not m:
        raise RuntimeError(f"Could not parse reference {num}: {ref}")
    authors, title, journal, year, volpages, tail = m.groups()
    authors = authors.rstrip(".")
    journal_short = journal_abbrev.get(journal, journal)
    doi = ""
    if "DOI:" in tail:
        doi = tail.split("DOI:", 1)[1].strip().rstrip(".")
    pmid_match = re.search(r"PMID:\s*(\d+)", tail)
    pmid = pmid_match.group(1) if pmid_match else ""
    extras = []
    if doi:
        extras.append(f"doi:{doi}")
    if pmid:
        extras.append(f"PMID: {pmid}")
    citation = f"{num}. {authors}. {title}. {journal_short}. {year};{volpages}."
    if extras:
        citation += " " + ". ".join(extras) + "."
    formatted.append(citation)
    audit.append({"number": num, "type": "journal_article", "journal": journal_short, "doi": doi, "pmid": pmid, "status": "formatted"})

MD.write_text(head + "## References\n\n" + "\n".join(formatted) + "\n", encoding="utf-8", newline="\n")
OUTCSV.parent.mkdir(parents=True, exist_ok=True)
with OUTCSV.open("w", newline="", encoding="utf-8-sig") as fh:
    writer = csv.DictWriter(fh, fieldnames=["number", "type", "journal", "doi", "pmid", "status"])
    writer.writeheader()
    writer.writerows(audit)
AUDIT.write_text(
    "# Plan B reference format audit\n\n"
    "- References: 40\n"
    "- Style: Frontiers/Vancouver-compatible numbered references\n"
    "- Journal names: standardized to NLM-style abbreviations\n"
    "- DOI and PMID: retained where supplied in the source record\n"
    "- GEO accessions: references 28-30 formatted as database records with direct GEO links\n"
    "- Author-input check: verify complete author lists for records using `et al.` and confirm any missing article page/elocation in references 33 and 40 before submission.\n",
    encoding="utf-8",
    newline="\n",
)
print("references", len(formatted), "written")
