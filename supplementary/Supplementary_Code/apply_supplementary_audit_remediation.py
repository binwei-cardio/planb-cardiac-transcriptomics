# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import csv, hashlib, shutil
import pandas as pd
ROOT = PLANB_ROOT
SRC=ROOT/'06_Manuscript'/'Supplementary'
SUP=ROOT/'06_Manuscript'/'Supplementary_corrected_v2_20261118'
if not SUP.exists(): shutil.copytree(SRC,SUP)
SUP.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'03_output'
# S1 metadata additions
s1=pd.read_csv(SUP/'Supplementary_Table_S1_Datasets.csv')
meta={
'GSE292067':(25,25,'Nine GEO samples lacked raw files; processed GEO matrices used','7','None'),
'GSE288222':(12,12,'None','7','None'),
'GSE298023':(18,13,'Five ICM-scar samples excluded: GSM9004762, GSM9004764, GSM9004768, GSM9004776, GSM9004777','6','Senescence not scored'),
'GSE161470':(5,5,'Four control GSM records collapsed to one Control pseudobulk group in S4A','7','None'),
'GSE297745':(4,4,'None','6','Senescence not scored'),
'GSE299032':(30,5,'Only five heart scRNA-seq GSMs used; PBMC, BCR and TCR records not used','7','None'),
'GSE135805':(4,4,'One section per group; gene coverage 4,029-12,734; severe depth imbalance','4','CM_stress, Tcell_cytotoxic and Senescence not assessed')}
for c in ['GEO_GSM_total','GSM_used','Excluded_or_limitation','Programmes_assessed','Module_exceptions']:
    if c not in s1.columns: s1[c]=''
    s1[c]=s1[c].astype(object)
for i,r in s1.iterrows():
    total,used,excluded,programmes,exceptions=meta[r['Dataset']]
    s1.at[i,'GEO_GSM_total']=total; s1.at[i,'GSM_used']=used
    s1.at[i,'Excluded_or_limitation']=excluded; s1.at[i,'Programmes_assessed']=programmes
    s1.at[i,'Module_exceptions']=exceptions
s1.to_csv(SUP/'Supplementary_Table_S1_Datasets.csv',index=False,encoding='utf-8-sig')
avail=[]
for _,r in s1.iterrows():
    avail.append({'Dataset':r['Dataset'],'Programmes_assessed':r['Programmes_assessed'],'Module_exceptions':r['Module_exceptions'],'Cross_dataset_synthesis':'No' if r['Dataset']=='GSE135805' else 'Yes'})
pd.DataFrame(avail).to_csv(SUP/'Supplementary_Table_S1_Module_availability.csv',index=False,encoding='utf-8-sig')
# S2 CXCL8 ortholog note
s2=pd.read_csv(SUP/'Supplementary_Table_S2_Module_genes.csv')
s2.loc[s2['Human_symbol']=='CXCL8','Mouse_symbol_used']='NA'
s2.loc[s2['Human_symbol']=='CXCL8','Notes']='No direct one-to-one mouse ortholog; excluded from mouse senescence gene detection when absent'
s2.to_csv(SUP/'Supplementary_Table_S2_Module_genes.csv',index=False,encoding='utf-8-sig')
# Correct GSE135805 group labels in S4B/S4C from GSM mapping
mapg={'GSM4030472':'Normal','GSM4030473':'ICM','GSM4030474':'DCM','GSM4030475':'HCM'}
for name in ['Supplementary_Table_S4B_GSE135805_section_summary.csv','Supplementary_Table_S4C_GSE135805_gene_coverage.csv']:
    p=SUP/name
    if p.exists():
        d=pd.read_csv(p); d['Group']=d['GSM'].map(mapg).fillna(d.get('Group','')); d.to_csv(p,index=False,encoding='utf-8-sig')
# S4 summary panel wording
p=SUP/'Supplementary_Table_S4_Sensitivity_summary.csv'
if p.exists():
    d=pd.read_csv(p)
    d.loc[d['Sensitivity_dataset']=='GSE135805','Key_finding']='One section per group; gene coverage 4,029-12,734; CM_stress, cytotoxic and senescence genes mostly absent; depth imbalance'
    d.to_csv(p,index=False,encoding='utf-8-sig')
# Copy selected core tables
core=SUP/'Supplementary_Core_Tables'; core.mkdir(exist_ok=True)
core_names=['gse292067_pseudobulk_celltype.csv','gse292067_pseudobulk_sample.csv','gse292067_celltype_permutation.csv','gse292067_contrast_effects_v2.csv','gse292067_global_group_tests_v2.csv','gse292067_specificity_matrix_v2.csv','gse288222_controlscore_celltype_pseudobulk.csv','gse288222_controlscore_celltype_permutation.csv','gse288222_controlscore_control_genes.csv','gse288222_controlscore_sample_permutation.csv','gse298023_controlscore_pseudobulk_celltype.csv','gse298023_controlscore_celltype_permutation_with_fdr.csv','gse297745_controlscore_pseudobulk.csv','gse297745_controlscore_permutation_with_fdr.csv','gse297745_spatial_niche.csv','gse299032_controlscore_pseudobulk.csv','gse299032_controlscore_directional.csv','planb_master_module_tests_v4.csv','planb_primary_four_pairs_v1.csv','planb_cross_dataset_matrix_v4.csv','planb_cross_dataset_qvalues_v4.csv','planb_cross_dataset_evidence_tier_v4.csv']
for n in core_names:
    src=OUT/n
    if src.exists(): shutil.copy2(src,core/n)
# Copy scripts
code=SUP/'Supplementary_Code'; code.mkdir(exist_ok=True)
for p in (ROOT/'06_scripts').glob('*.py'):
    shutil.copy2(p,code/p.name)
shutil.copy2(ROOT/'REPRO_RULES.md',SUP/'REPRO_RULES.md')
# Rewrite supplement guide with corrected audit notes
md='''# Supplementary Information: Plan B candidate recurrent programmes in heart failure and cancer therapy-related cardiotoxicity

## Supplementary Table S1. Datasets, sample selection and evidence roles

Files:
- `Supplementary_Table_S1_Datasets.csv`
- `Supplementary_Table_S1_Module_availability.csv`

S1 now records total GEO GSM counts, GSMs used, excluded or unavailable samples, assessed programmes and interpretation boundaries. GSE298023 used 13/18 GSMs and excluded five ICM-scar samples; GSE299032 used five heart scRNA-seq GSMs from a 30-GSM series; GSE292067 processed matrices were used because nine GEO samples lacked raw files. GSE297745 and GSE299032 are descriptive and directional only.

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

## Core tables and code

`Supplementary_Core_Tables/` contains the principal pseudobulk, permutation, FDR, synthesis and spatial tables. `Supplementary_Code/` contains the analysis scripts; `REPRO_RULES.md` describes the clean-room rules. The archived source audit and reproducibility reports remain in the parent project.

## Statistical and interpretation notes

- Table 2 uses `gse292067_celltype_permutation.csv` as the primary source for the GSE292067 FDR values; `planb_master_module_tests_v4.csv` applies a different correction family for cross-dataset synthesis.
- Cross-dataset synthesis includes six programmes; Endothelial is not included in the matrix.
- z-score and rank-based scoring were considered but not formally benchmarked in the final analysis.
- The DoxCM-versus-NICM comparison is a negative result: no direct comparison survived FDR correction.
- TCM content is restricted to future research hypotheses; no efficacy inference is made.
'''
(SUP/'Supplementary_Information_PlanB_v1.md').write_text(md,encoding='utf-8')
# Manifest of current supplement
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()
rows=[]
for p in sorted(SUP.rglob('*')):
    if p.is_file() and p.name not in {'Supplementary_SHA256_manifest.csv'}:
        rows.append({'relative_path':p.relative_to(SUP).as_posix(),'size':p.stat().st_size,'sha256':sha(p)})
with open(SUP/'Supplementary_SHA256_manifest.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['relative_path','size','sha256']); w.writeheader(); w.writerows(rows)
# Update project snapshot
snap=ROOT/'08_reports'/'PlanB_Supplementary_SHA256_snapshot_corrected_20261118.csv'
with open(snap,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['relative_path','size','sha256']); w.writeheader(); w.writerows(rows)
print('supplement_manifest_files=',len(rows))
print('snapshot=',snap)


