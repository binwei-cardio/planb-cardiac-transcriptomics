# Plan B code and result repository

This repository contains the analysis scripts, derived result tables, figures, supplementary tables and audit reports for the Plan B cross-dataset study.

## Study

Cross-dataset single-cell and spatial transcriptomic analysis identifies candidate shared fibrotic and cytotoxic T-cell programmes in heart failure and cancer therapy-related cardiotoxicity: a hypothesis-generating exploratory cross-dataset secondary analysis.

Target article type: Original Research, Frontiers in Cardiovascular Medicine.

## Data sources

Raw public datasets are not redistributed here. They are available from NCBI GEO under accessions GSE292067, GSE288222, GSE298023, GSE161470, GSE297745, GSE299032 and GSE135805. See `DATA_SOURCES.md`.

## Reproducibility

Scripts derive the project root from `scripts/planb_paths.py` or the `PLANB_ROOT` environment variable. `PLANB_PROJECT_ROOT` can override the parent directory. Raw-file SHA-256 records and archive member validation are included in `supplementary/`.

## Repository setup needed before public release

- Choose a licence. No licence has been selected in this staging package.
- Upload the repository to GitHub or GitLab under the authors' account.
- Add the public repository URL to the title page and data/code availability statement.
- Create a release tag or commit identifier for the submitted version.
