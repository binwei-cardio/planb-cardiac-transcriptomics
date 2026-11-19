# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import csv, pandas as pd
ROOT = PLANB_ROOT
OUT=ROOT/'06_Manuscript'/'Supplementary'
OUT.mkdir(parents=True,exist_ok=True)
s1=[
{'Dataset':'GSE292067','Species':'Human','Modality':'snRNA-seq','Tissue':'Heart','Groups':'Donor 8; DoxCM 11; NICM 6','N_cells_or_spots':190478,'Primary_role':'Primary DoxCM/NICM/donor analysis','Evidence_tier':'Human primary','PMID':'40808662','Accession':'GSE292067','Integrated_quantitative_synthesis':'Yes','Interpretation_boundary':'Module-level comparison; no causal inference'},
{'Dataset':'GSE288222','Species':'Human','Modality':'snRNA-seq','Tissue':'Left ventricle','Groups':'Non-diseased 6; end-stage HF 6','N_cells_or_spots':52967,'Primary_role':'Independent human HF analysis','Evidence_tier':'Human primary','PMID':'41017471','Accession':'GSE288222','Integrated_quantitative_synthesis':'Yes','Interpretation_boundary':'Gene-level reanalysis; isoform biology not modelled'},
{'Dataset':'GSE298023','Species':'Human','Modality':'snRNA-seq','Tissue':'Left ventricle','Groups':'Donor 2; ICM 5; DCM 6','N_cells_or_spots':121353,'Primary_role':'Aetiology comparison','Evidence_tier':'Human primary/sensitivity','PMID':'41310709','Accession':'GSE298023','Integrated_quantitative_synthesis':'Yes','Interpretation_boundary':'Only two donor samples; sensitivity interpretation'},
{'Dataset':'GSE161470','Species':'Human','Modality':'snRNA-seq','Tissue':'Left ventricle','Groups':'Control 4; HF 1','N_cells_or_spots':11716,'Primary_role':'Sensitivity analysis','Evidence_tier':'Human sensitivity','PMID':'34088950','Accession':'GSE161470','Integrated_quantitative_synthesis':'No','Interpretation_boundary':'Single HF sample; descriptive only'},
{'Dataset':'GSE297745','Species':'Mouse','Modality':'Visium spatial transcriptomics','Tissue':'Heart','Groups':'ICI 2; IL-17A-neutralised 2','N_cells_or_spots':10741,'Primary_role':'Spatial programme architecture','Evidence_tier':'Mouse supportive spatial','PMID':'Not indexed','Accession':'GSE297745','Integrated_quantitative_synthesis':'Yes','Interpretation_boundary':'2-versus-2 design; descriptive and directional only; no causal inference'},
{'Dataset':'GSE299032','Species':'Mouse','Modality':'scRNA-seq','Tissue':'Heart','Groups':'ICI model 4; control 1','N_cells_or_spots':111892,'Primary_role':'Directional cardiotoxicity support','Evidence_tier':'Mouse directional','PMID':'Not indexed','Accession':'GSE299032','Integrated_quantitative_synthesis':'Yes','Interpretation_boundary':'Single control; descriptive and directional only; no causal inference'},
{'Dataset':'GSE135805','Species':'Human','Modality':'Spatial transcriptomics','Tissue':'Heart','Groups':'Normal 1; HCM 1; DCM 1; ICM 1','N_cells_or_spots':1096,'Primary_role':'Platform/depth sensitivity','Evidence_tier':'Human platform sensitivity','PMID':'31862877','Accession':'GSE135805','Integrated_quantitative_synthesis':'No','Interpretation_boundary':'One section per group; 4,029-gene panel; severe depth imbalance; no group inference'}]
with open(OUT/'Supplementary_Table_S1_Datasets.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(s1[0])); w.writeheader(); w.writerows(s1)
modules={
'Fibrosis_ECM':['COL1A1','COL1A2','COL3A1','COL5A1','COL8A1','FN1','POSTN','FAP','TGFB1','TGFBR1','ACTA2','TIMP1','LOX','COMP','THBS1','LUM','DCN'],
'Inflammation':['IL6','IL1B','TNF','CCL2','CCR2','CXCL10','IFNG','STAT1','NFKB1','NLRP3','CD68','LYZ','ITGAM','TLR4','CCL5','IL10'],
'Endothelial':['PECAM1','VWF','CDH5','KDR','FLT1','ANGPT2','VEGFA','ESM1','ENG','NOS3'],
'Hypoxia_Metabolism':['HIF1A','VEGFA','SLC2A1','LDHA','PGK1','ENO1','HK2','PDK1','BNIP3','NDRG1','ANGPTL4'],
'CM_stress':['NPPA','NPPB','MYH7','ACTC1','TNNT2','TTN','MYL2','PLN','MYH6'],
'Tcell_cytotoxic':['CD3E','CD3D','CD8A','NKG7','GZMB','PRF1','IFNG','CCL5'],
'Senescence':['CDKN1A','CDKN2A','TP53','GLB1','SERPINE1','IL6','CXCL8','LMNB1']}
mouse={'LYZ':'Lyz2','TP53':'Trp53','CXCL8':'Cxcl8'}
def mouse_orth(g):
    if g in mouse: return mouse[g]
    return g[:1]+g[1:].lower()
rows=[]
for m,genes in modules.items():
    for g in genes:
        rows.append({'Programme':m,'Human_symbol':g,'Mouse_symbol_used':mouse_orth(g),'Notes':'Requested programme gene; actual detection varies by dataset'})
with open(OUT/'Supplementary_Table_S2_Module_genes.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
sp=pd.read_csv(ROOT/'03_output'/'gse297745_spatial_niche.csv')
sp.to_csv(OUT/'Supplementary_Table_S3_Spatial_niche_full.csv',index=False,encoding='utf-8-sig')
sp[~sp['Module'].str.contains('->',regex=False)].groupby(['Group','Module'],as_index=False)['Morans_I'].mean().to_csv(OUT/'Supplementary_Table_S3_Moran_I_summary.csv',index=False,encoding='utf-8-sig')
sp[sp['Module'].str.contains('->',regex=False)].groupby(['Group','Module'],as_index=False)['Enrichment'].mean().to_csv(OUT/'Supplementary_Table_S3_Neighbourhood_summary.csv',index=False,encoding='utf-8-sig')
pd.read_csv(ROOT/'03_output'/'gse161470_controlscore_celltype_directional.csv').to_csv(OUT/'Supplementary_Table_S4A_GSE161470_directional.csv',index=False,encoding='utf-8-sig')
pd.read_csv(ROOT/'03_output'/'gse135805_controlscore_section_summary.csv').to_csv(OUT/'Supplementary_Table_S4B_GSE135805_section_summary.csv',index=False,encoding='utf-8-sig')
pd.read_csv(ROOT/'03_output'/'gse135805_controlscore_gene_coverage.csv').to_csv(OUT/'Supplementary_Table_S4C_GSE135805_gene_coverage.csv',index=False,encoding='utf-8-sig')
summary=[{'Sensitivity_dataset':'GSE161470','Comparison':'HF vs Control','Key_finding':'T/NK cytotoxic directionally higher; fibroblast Fibrosis-ECM directionally lower','Inference':'Descriptive only: one HF sample'}, {'Sensitivity_dataset':'GSE135805','Comparison':'Normal vs HCM vs DCM vs ICM','Key_finding':'One section per group; 4,029-gene panel; CM_stress, cytotoxic and senescence genes mostly absent; depth imbalance','Inference':'Platform/depth sensitivity only; no group inference'}]
with open(OUT/'Supplementary_Table_S4_Sensitivity_summary.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
md='''# Supplementary Information: Plan B candidate recurrent programmes in heart failure and cancer therapy-related cardiotoxicity\n\n## Supplementary Table S1. Datasets and evidence roles\n\nFile: `Supplementary_Table_S1_Datasets.csv`\n\nThis table lists the seven public datasets, species, modality, tissue, group sizes, cell or spot counts, evidence tier, source identifiers and interpretation boundaries. GSE292067, GSE288222 and GSE298023 are human primary evidence; GSE161470 is a one-HF-sample sensitivity dataset; GSE297745 and GSE299032 are mouse supportive datasets with descriptive and directional interpretation only; GSE135805 is a platform/depth sensitivity dataset.\n\n## Supplementary Table S2. Programme gene lists\n\nFile: `Supplementary_Table_S2_Module_genes.csv`\n\nSeven programmes are listed with their requested human symbols and the mouse symbols used where applicable. Actual gene detection varies by dataset, platform and processed matrix; GSE135805 coverage is reported separately in Table S4C.\n\n## Supplementary Table S3. Spatial programme architecture in mouse ICI myocarditis\n\nFiles:\n\n- `Supplementary_Table_S3_Spatial_niche_full.csv`\n- `Supplementary_Table_S3_Moran_I_summary.csv`\n- `Supplementary_Table_S3_Neighbourhood_summary.csv`\n\nThe full spot-level Moran's I and neighbourhood results are provided together with group-level summaries. The mouse Visium dataset is a 2-versus-2 design. These data are descriptive and directional only; no causal inference is possible.\n\n## Supplementary Table S4. Sensitivity analyses\n\nFiles:\n\n- `Supplementary_Table_S4A_GSE161470_directional.csv`\n- `Supplementary_Table_S4B_GSE135805_section_summary.csv`\n- `Supplementary_Table_S4C_GSE135805_gene_coverage.csv`\n- `Supplementary_Table_S4_Sensitivity_summary.csv`\n\nGSE161470 contains one failing heart and is reported for descriptive sensitivity only. GSE135805 contains one section per group, a 4,029-gene panel and severe depth imbalance; CM_stress, cytotoxic T-cell and senescence programme genes are largely absent. Neither dataset is used for primary statistical inference.\n\n## Statistical and interpretative notes\n\n- All main inferential comparisons use sample-level or sample-by-cell-type pseudobulk values.\n- Exact permutation tests are used for two-group comparisons; Benjamini-Hochberg correction is used where stated.\n- Cross-dataset synthesis describes directional consistency and is not a pooled effect-size meta-analysis.\n- The DoxCM-versus-NICM comparison is explicitly reported as a negative result: no direct comparison survived FDR correction.\n- TCM content is restricted to future research hypotheses; no efficacy inference is made.\n'''
(OUT/'Supplementary_Information_PlanB_v1.md').write_text(md,encoding='utf-8')
print('supplement_dir=',OUT)
for p in sorted(OUT.iterdir()): print(p.name,p.stat().st_size)
