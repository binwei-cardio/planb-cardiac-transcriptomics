# -*- coding: utf-8 -*-
"""Clean-room spatial niche analysis for GSE297745 using raw tissue positions."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
if len(sys.argv)!=2:
    raise SystemExit('usage: gse297745_spatial_niche_cleanroom.py <repro_root>')
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PLANB_ROOT; DATA=ROOT/'02_unpacked'/'GSE297745'; OUT=ROOT/'03_output'; FIG=ROOT/'04_figures'
OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(parents=True,exist_ok=True)
MODULES=['Fibrosis_ECM','Inflammation','Endothelial','Hypoxia_Metabolism','CM_stress','Tcell_cytotoxic']
SAMPLES={'GSM8998316':'WO_66093','GSM8998317':'WO_66094','GSM8998318':'WO_66095','GSM8998319':'WO_66096'}
scores=pd.read_csv(OUT/'gse297745_controlscore_spots.csv.gz')
pos=[]
for gsm,suf in SAMPLES.items():
    p=pd.read_csv(DATA/f'{gsm}_{suf}_tissue_positions.csv.gz').rename(columns={'barcode':'spot'}); p['GSM']=gsm
    pos.append(p[['GSM','spot','pxl_row_in_fullres','pxl_col_in_fullres']])
pos=pd.concat(pos,ignore_index=True); df=scores.merge(pos,on=['GSM','spot'],how='inner')
def morans_i(vals,pts,k=6):
    v=np.asarray(vals,float); good=np.isfinite(v)
    if good.sum()<20: return np.nan
    p=pts[good]; v2=v[good]; tree=cKDTree(p); _,idx=tree.query(p,k=k+1)
    W=np.zeros((len(p),len(p)))
    for a in range(len(p)): W[a,idx[a,1:]]=1
    W=(W+W.T)/2; z=v2-v2.mean(); S0=W.sum()
    if S0==0 or np.allclose(z,0): return np.nan
    return float((len(p)/S0)*(z@W@z)/(z@z))
rows=[]
for gsm,g in df.groupby('GSM'):
    pts=g[['pxl_col_in_fullres','pxl_row_in_fullres']].values
    for m in MODULES: rows.append({'GSM':gsm,'Group':g.Group.iloc[0],'Module':m,'Morans_I':morans_i(g[m].values,pts)})
    tree=cKDTree(pts); _,idx=tree.query(pts,k=7)
    for a in MODULES:
        hi_a=g[a].values>=np.nanpercentile(g[a].values,75)
        for b in ['Fibrosis_ECM','Inflammation','Tcell_cytotoxic']:
            if a==b: continue
            hi_b=g[b].values>=np.nanpercentile(g[b].values,75); neigh_hi=hi_b[idx[hi_a][:,1:]].mean(); base=hi_b.mean()
            rows.append({'GSM':gsm,'Group':g.Group.iloc[0],'Module':f'{a}->{b}','Morans_I':np.nan,'Enrichment':float(neigh_hi-base),'NeighborFrac':float(neigh_hi),'Base':float(base)})
res=pd.DataFrame(rows); res.to_csv(OUT/'gse297745_spatial_niche.csv',index=False)
print("Moran's I:"); mi=res[res.Morans_I.notna()].groupby(['Group','Module']).Morans_I.mean().reset_index(); print(mi.pivot(index='Module',columns='Group',values='Morans_I').round(3).to_string())
print('\nNeighbour enrichment:'); ne=res[res.Module.str.contains('->',na=False)].groupby(['Group','Module']).Enrichment.mean().reset_index(); print(ne.pivot(index='Module',columns='Group',values='Enrichment').round(4).to_string())
fig,axes=plt.subplots(1,2,figsize=(13,4.5)); mi.pivot(index='Module',columns='Group',values='Morans_I').plot(kind='bar',ax=axes[0]); axes[0].set_title("Moran's I"); axes[0].set_ylabel("Moran's I"); ne.pivot(index='Module',columns='Group',values='Enrichment').plot(kind='bar',ax=axes[1]); axes[1].set_title('Neighbour enrichment'); axes[1].set_ylabel('excess neighbour fraction'); plt.tight_layout(); plt.savefig(FIG/'GSE297745_spatial_niche.png',dpi=300,bbox_inches='tight'); plt.close(fig)
print('wrote',OUT/'gse297745_spatial_niche.csv')
