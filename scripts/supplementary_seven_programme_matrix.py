# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import pandas as pd
ROOT = PLANB_ROOT; OUT=ROOT/'03_output'; SUP=ROOT/'06_Manuscript'/'Supplementary_corrected_v2_20261118'
mat=pd.read_csv(OUT/'planb_cross_dataset_matrix_v4.csv',index_col=0); q=pd.read_csv(OUT/'planb_cross_dataset_qvalues_v4.csv',index_col=0); tier=pd.read_csv(OUT/'planb_cross_dataset_evidence_tier_v4.csv',index_col=0); cols=list(mat.columns)
endo={}
f67=pd.read_csv(OUT/'gse292067_contrast_effects_v2.csv')
for cmp,col in [('DoxCM_vs_Donor',cols[0]),('NICM_vs_Donor',cols[1]),('DoxCM_vs_NICM',cols[2])]:
    r=f67[(f67.CellType=='Endothelial')&(f67.Module=='Endothelial')&(f67.Comparison==cmp)]; endo[col]=(float(r['diff'].iloc[0]),float(r['FDR'].iloc[0])) if len(r) else (float('nan'),float('nan'))
f88=pd.read_csv(OUT/'gse288222_controlscore_celltype_permutation.csv'); r=f88[(f88.CellType=='Endothelial')&(f88.Module=='Endothelial')]; endo[cols[2]]=(float(r['diff'].iloc[0]),float(r['FDR'].iloc[0])) if len(r) else (float('nan'),float('nan'))
f98=pd.read_csv(OUT/'gse298023_controlscore_celltype_permutation_with_fdr.csv')
for cmp,col in [('ICM_vs_Donor',cols[3]),('DCM_vs_Donor',cols[4])]:
    r=f98[(f98.CellType=='Endothelial')&(f98.Module=='Endothelial')&(f98.Comparison==cmp)]; endo[col]=(float(r['diff'].iloc[0]),float(r['q'].iloc[0])) if len(r) else (float('nan'),float('nan'))
f97=pd.read_csv(OUT/'gse297745_controlscore_permutation_with_fdr.csv'); r=f97[f97.Module=='Endothelial']; endo[cols[5]]=(float(r['diff'].iloc[0]),float(r['q'].iloc[0])) if len(r) else (float('nan'),float('nan'))
f99=pd.read_csv(OUT/'gse299032_controlscore_directional.csv'); r=f99[f99.Module=='Endothelial']; endo[cols[6]]=(float(r['diff'].iloc[0]),float('nan')) if len(r) else (float('nan'),float('nan'))
mat.loc['Endothelial']=[endo[c][0] for c in cols]; q.loc['Endothelial']=[endo[c][1] for c in cols]; tier.loc['Endothelial']=['mixed/sensitivity']*len(cols)
mat.to_csv(SUP/'Supplementary_Table_S7_Seven_programme_cross_dataset_matrix.csv',encoding='utf-8-sig')
q.to_csv(SUP/'Supplementary_Table_S7_Seven_programme_cross_dataset_qvalues.csv',encoding='utf-8-sig')
tier.to_csv(SUP/'Supplementary_Table_S7_Seven_programme_cross_dataset_evidence_tier.csv',encoding='utf-8-sig')
print(mat.loc['Endothelial'].to_string())

