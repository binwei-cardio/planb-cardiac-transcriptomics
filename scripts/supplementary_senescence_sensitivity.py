# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import itertools, glob
import numpy as np, pandas as pd
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from planb_ucell_lib import load_mtx_dir
from planb_controlscore_lib import control_module_scores
ROOT = PLANB_ROOT
RAW298=ROOT/'02_unpacked'/'GSE298023'; RAW297=ROOT/'02_unpacked'/'GSE297745'
SUP=ROOT/'06_Manuscript'/'Supplementary_corrected_v2_20261118'; OUT=ROOT/'03_output'
SEN={'Senescence':['CDKN1A','CDKN2A','TP53','GLB1','SERPINE1','IL6','CXCL8','LMNB1']}
SEN_MOUSE={'Senescence':['Cdkn1a','Cdkn2a','Trp53','Glb1','Serpine1','Il6','Cxcl8','Lmnb1']}
G298={'ICM':['GSM9004761','GSM9004763','GSM9004765','GSM9004769','GSM9004770'],'DCM':['GSM9004766','GSM9004767','GSM9004771','GSM9004772','GSM9004773','GSM9004778'],'Donor':['GSM9004774','GSM9004775']}
G297={'GSM8998316':('ICI','WO_66093'),'GSM8998317':('ICI','WO_66094'),'GSM8998318':('Rescue','WO_66095'),'GSM8998319':('Rescue','WO_66096')}
def files_for(gsm):
    m=glob.glob(str(RAW298/(gsm+'*_matrix.mtx.gz')))
    return m[0][:-len('_matrix.mtx.gz')] if m else None
def exact_perm(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float); obs=abs(a.mean()-b.mean()); pool=np.concatenate([a,b]); n=len(a); c=t=0
    for comb in itertools.combinations(range(len(pool)),n):
        s=set(comb); g1=[pool[i] for i in s]; g2=[pool[i] for i in range(len(pool)) if i not in s]
        if abs(np.mean(g1)-np.mean(g2))>=obs-1e-12: c+=1
        t+=1
    return obs,c/t
ctdf=pd.read_csv(OUT/'gse298023_cell_module_scores.csv.gz'); ctmap={(r.GSM,r.cell):r.celltype for r in ctdf.itertuples()}; rows=[]
for group,gsms in G298.items():
    for gsm in gsms:
        base=files_for(gsm)
        if not base: continue
        X,syms,bcs=load_mtx_dir(base); sc,_=control_module_scores(X,syms,SEN,n_ctrl=10,n_bins=20,seed=42)
        d=pd.DataFrame({'GSM':gsm,'Group':group,'cell':bcs,'Senescence':sc['Senescence'].values}); d['celltype']=[ctmap.get((gsm,c),'Unassigned') for c in bcs]; d=d[d.celltype!='Unassigned']
        for ct,g in d.groupby('celltype'):
            if len(g)>=3: rows.append({'Dataset':'GSE298023','GSM':gsm,'Group':group,'CellType':ct,'Senescence':float(g.Senescence.mean()),'n_cells':len(g)})
        print('GSE298023',gsm,group,len(d))
pb298=pd.DataFrame(rows); pb298.to_csv(SUP/'Supplementary_Table_S6A_GSE298023_Senescence_pseudobulk.csv',index=False,encoding='utf-8-sig'); tests=[]
for ct in sorted(pb298.CellType.unique()):
    sub=pb298[pb298.CellType==ct]
    for g1,g2,label in [('ICM','Donor','ICM_vs_Donor'),('DCM','Donor','DCM_vs_Donor')]:
        a=sub[sub.Group==g1].Senescence.values; b=sub[sub.Group==g2].Senescence.values
        if len(a)>=2 and len(b)>=2:
            diff,p=exact_perm(a,b); tests.append({'Dataset':'GSE298023','Comparison':label,'CellType':ct,'n1':len(a),'n2':len(b),'mean1':a.mean(),'mean2':b.mean(),'diff':diff,'p':p,'Inference':'Donor n=2; sensitivity only'})
rows297=[]
for gsm,(group,suf) in G297.items():
    X,syms,bcs=load_mtx_dir(str(RAW297/f'{gsm}_{suf}')); sc,_=control_module_scores(X,syms,SEN_MOUSE,n_ctrl=10,n_bins=20,seed=42); total=np.asarray(X.sum(axis=1)).ravel(); keep=total>=50
    rows297.append({'GSM':gsm,'Group':group,'Senescence':float(np.nanmean(sc['Senescence'].values[keep])),'n_spots':int(keep.sum())})
pb297=pd.DataFrame(rows297); pb297.to_csv(SUP/'Supplementary_Table_S6B_GSE297745_Senescence_pseudobulk.csv',index=False,encoding='utf-8-sig')
a=pb297[pb297.Group=='ICI'].Senescence.values; b=pb297[pb297.Group=='Rescue'].Senescence.values; diff,p=exact_perm(a,b); tests.append({'Dataset':'GSE297745','Comparison':'ICI_vs_Rescue','CellType':'All_spots','n1':len(a),'n2':len(b),'mean1':a.mean(),'mean2':b.mean(),'diff':diff,'p':p,'Inference':'2-versus-2 descriptive only; no causal inference'})
out=pd.DataFrame(tests); out.to_csv(SUP/'Supplementary_Table_S6_Senescence_sensitivity_tests.csv',index=False,encoding='utf-8-sig'); print(out.to_string(index=False))
