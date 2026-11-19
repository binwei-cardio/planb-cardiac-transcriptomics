# Plan B global freeze memo

Date: 2026-11-18  
Applies to: Chinese manuscript and English Frontiers manuscript

## Frozen rules and implementation status

### 1. Table 2 numerical lock

Status: PASS.

- All effect sizes, p values and FDR values in the main Results remain unchanged.
- The six key Table 2 results were cross-checked against the main text.
- No numerical result was changed during language or reviewer-style revision.

### 2. Unified study label

Frozen label:

`hypothesis-generating exploratory cross-dataset secondary analysis`

Status: implemented in:

- English title subtitle
- English Abstract Methods
- English Methods 2.1
- English Discussion 4.1
- English Conclusion
- Chinese title subtitle
- Chinese Abstract Methods
- Chinese Methods 2.1
- Chinese Discussion 4.1
- Chinese Conclusion

### 3. Mouse datasets: descriptive and directional only

Status: implemented for both mouse datasets.

- GSE297745, 2-versus-2 Visium: descriptive and directional only; no causal inference.
- GSE299032, single-control scRNA: descriptive and directional only; no causal inference.
- Figure 4 legend explicitly states that the 2-versus-2 design cannot support causal inference.
- Discussion 4.6 explicitly states that the 2-versus-2 design cannot support causal inference.

### 4. DoxCM-versus-NICM negative result

Status: retained without weakening.

The following statement or an equivalent is present in:

- Abstract Results
- Results 3.2, under the heading `Key negative result`
- Discussion 4.3
- Conclusion

No DoxCM-versus-NICM comparison was reclassified as a positive finding. The phrase `some programmes potentially stronger in DoxCM` was removed from the direct-comparison interpretation.

### 5. Traditional Chinese medicine boundary

Status: implemented.

- English heading changed to `Future research hypotheses relevant to traditional Chinese medicine`.
- Chinese heading changed to `与中医药相关的未来研究假设`.
- Both manuscripts state that this section is restricted to future research hypotheses.
- No efficacy inference is made.
- The Conclusion states that no TCM intervention efficacy is established.

## Numerical consistency spot-check

| Table 2 result | Main-text location | Status |
|---|---|---|
| DoxCM vs donor, fibroblast Fibrosis-ECM, +0.705, FDR 0.0042 | Results 3.2 | PASS |
| DoxCM vs donor, cardiomyocyte senescence, +0.169, FDR 0.0042 | Results 3.2 | PASS |
| DoxCM vs NICM, fibroblast Fibrosis-ECM, +0.367, p 0.071, FDR 0.590 | Results 3.2 and Discussion 4.3 | PASS |
| DoxCM vs NICM, T/NK cytotoxic, +1.007, p 0.077, FDR 0.590 | Results 3.2 and Discussion 4.3 | PASS |
| HF vs non-diseased, fibroblast Fibrosis-ECM, +0.263, p 0.036, FDR 0.689 | Results 3.3 | PASS |
| DCM vs donor, cardiomyocyte CM_stress, +0.868, p 0.036, FDR 0.214 | Results 3.4 and Table 2 | PASS |

## Freeze rule

From this point onward, changes to the following require explicit author approval:

- any numerical value;
- any DoxCM-versus-NICM wording;
- any mouse-dataset causal boundary;
- any TCM efficacy statement;
- the unified study label.

## Supplementary synchronization status

Status: PASS (2026-11-18).

- S1-S9 and the Supplementary guide are synchronized with both manuscripts.
- S8 contains 47,949 control-gene selection rows across 65 scoring units.
- S9 contains SHA-256 records for all 70 canonical `01_raw` files (5,542,396,236 bytes), including labelled partial and transfer artifacts.
- S10 validates 13 canonical artifacts and 240 TAR members; one GSE292067 duplicate with 8/100 members is quarantined.
- All 57 analysis scripts compile and contain no hard-coded drive path; `PLANB_ROOT` and `PLANB_PROJECT_ROOT` provide portable overrides.
- The corrected Supplementary manifest and project snapshot contain 106 entries with no size or SHA-256 mismatches.
- Post-audit validation passes 33/33 checks.
