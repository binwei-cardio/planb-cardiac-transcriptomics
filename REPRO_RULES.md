# Plan B clean-room reproduction rules

## 1. Raw data are immutable
- `01_raw` stores the original downloaded files.
- Raw files are never edited, renamed, trimmed, or overwritten after validation.
- Every raw download is recorded with file size, download date, source URL, and SHA-256.
- If a download is interrupted, resume with `curl -C -`; do not delete a valid partial file unless it is known to be corrupt.

## 2. Extraction is separate
- `02_unpacked` contains files extracted from raw archives.
- Extracted files are compared file-by-file with the original project using SHA-256.
- Archive-level hash differences are acceptable only when every extracted data file matches.

## 3. Analysis outputs are reproducible
- `03_output` contains only clean-room outputs generated from raw data.
- No copied outputs from the original project are allowed.
- Each script is executed from a clean-room path and produces deterministic outputs where seeds are fixed.
- Clean-room outputs are compared with original outputs using row count, column names, shape, exact equality, and maximum numeric difference.

## 4. Figures must be regenerated
- `04_figures/source_data` stores the exact table used for each figure panel.
- `04_figures/png`, `pdf`, `svg`, and `tiff` store exported figure formats.
- TIFF files should normally be 600 dpi and use lossless compression.
- Figure scripts must read from clean-room outputs, not from the original project.
- Every final figure must pass the font-size and rendered-collision audit.
- A copied old figure is not accepted as clean-room reproduction.

## 5. Logs and reports
- `07_logs` stores command outputs, script errors, runtime notes, and version notes.
- `08_reports` stores comparison reports, verification summaries, and final reproduction summaries.
- Every dataset gets its own report: download, extraction, analysis, comparison, and figure reproduction.

## 6. Required record for each dataset
- GEO accession
- Source URL
- Download date
- Raw file size
- Raw SHA-256
- Extracted file count
- Extracted SHA-256 comparison
- Analysis script name
- Input/output paths
- Clean-room result comparison
- Figure export paths and figure audit status

## 7. Portable roots and complete provenance records
- Analysis scripts derive `PLANB_ROOT` from `planb_paths.py` or the `PLANB_ROOT` environment variable; `PLANB_PROJECT_ROOT` overrides the parent project path.
- No analysis script contains a hard-coded drive path.
- `Supplementary_Table_S8_Control_gene_selections.csv` records every expression-matched control-gene selection with seed, bin count and identifier type.
- `Supplementary_Table_S9_Raw_file_SHA256.csv` records every existing file under `01_raw`, including partial and transfer artifacts.
- A SHA-256 record establishes byte identity only. Source freshness and download completeness are reported separately.
