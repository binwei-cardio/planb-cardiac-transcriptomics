# -*- coding: utf-8 -*-
"""Plan B Figure 3 v2: independent human HF and cardiomyopathy evidence."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_figure_style_v2 import *
h1=pd.read_csv(OUT/'gse288222_controlscore_celltype_permutation.csv'); h2=pd.read_csv(OUT/'gse298023_controlscore_celltype_permutation_with_fdr.csv')
primary=pd.read_csv(OUT/'planb_primary_four_pairs_v1.csv'); matdf=pd.read_csv(OUT/'planb_cross_dataset_matrix_v4.csv',index_col=0)
mods=MODULES; ct_order=['Cardiomyocytes','Fibroblasts','Myeloid','T_NK','Endothelial','Pericyte_SMC']; short_mods=['Fib','Inf','Endo','Hyp','CM','Cyto','Sen']
panels=[('GSE288222\nHF vs ND',h1,None),('GSE298023\nICM vs Donor',h2,'ICM_vs_Donor'),('GSE298023\nDCM vs Donor',h2,'DCM_vs_Donor')]
fig=plt.figure(figsize=(7.4,6.2)); gs=fig.add_gridspec(2,3,height_ratios=[1.0,0.92],left=0.07,right=0.90,bottom=0.08,top=0.90,hspace=0.45,wspace=0.30)
for k,(title,d,cmp) in enumerate(panels):
    ax=fig.add_subplot(gs[0,k]); sub=d[d.Comparison==cmp].copy() if cmp else d.copy()
    mat=np.full((len(ct_order),len(mods)),np.nan); ann=np.full(mat.shape,'',dtype=object)
    for i,ct in enumerate(ct_order):
        for j,mod in enumerate(mods):
            r=sub[(sub.CellType==ct)&(sub.Module==mod)]
            if len(r):
                mat[i,j]=float(r['diff'].iloc[0]); q=float(r['FDR'].iloc[0] if 'FDR' in r.columns else r['q'].iloc[0]); p=float(r['perm_p'].iloc[0])
                pass
    im=heatmap(ax,mat,[c.replace('_',' ') for c in ct_order],short_mods,title=f"{'ABC'[k]}. {title}",annotations=ann,vmin=-0.7,vmax=0.7,fontsize=5.2)
    if k>0: ax.set_yticklabels([])
cax=fig.add_axes([0.92,0.60,0.012,0.28]); cb=fig.colorbar(im,cax=cax); cb.set_label('Disease - control',fontsize=6,labelpad=3); cb.ax.tick_params(labelsize=5.5,length=1.5)

# D: focused-pair dot matrix.
ax=fig.add_subplot(gs[1,:2]); order=primary.copy()
cmap_order=[('DoxCM vs Donor','Dox'),('NICM vs Donor','NICM'),('DoxCM vs NICM','DvN'),('HF vs ND','HF'),('ICM vs Donor','ICM'),('DCM vs Donor','DCM'),('ICI vs Rescue','ICI')]
pairs=['Fibroblast fibrosis-ECM','T/NK cytotoxic','Cardiomyocyte stress','Myeloid inflammation']
for yi,pair in enumerate(pairs):
    for xi,(cmp,lbl) in enumerate(cmap_order):
        r=order[(order.Pair==pair)&(order.Comparison==cmp)]
        if not len(r): continue
        v=float(r['diff'].iloc[0]); q=float(r['source_q'].iloc[0]); p=float(r['p'].iloc[0])
        edge = 'black' if q<.05 else ('#555555' if q<.10 else ('#999999' if p<.05 else 'white'))
        ax.scatter(xi,yi,s=45+70*min(abs(v),1.0),c=[v],cmap='RdBu_r',vmin=-1.0,vmax=1.0,edgecolor=edge,linewidth=.9,zorder=3)
ax.set_xticks(range(len(cmap_order))); ax.set_xticklabels([x[1] for x in cmap_order],fontsize=5.2)
ax.set_yticks(range(len(pairs))); ax.set_yticklabels(['Fibrosis','Cytotoxic T','CM stress','Inflammation'],fontsize=5.2); ax.invert_yaxis()
ax.set_xlim(-.5,len(cmap_order)-.5); ax.set_ylim(len(pairs)-.5,-.5); ax.set_title('D. Focused biological-pair effects',fontsize=6.8,fontweight='bold',loc='left')
ax.spines[['top','right','left','bottom']].set_visible(False); ax.tick_params(length=0)

# E: direction consistency.
ax=fig.add_subplot(gs[1,2]); labels=[]; pos=[]; neg=[]
for module,row in matdf.iterrows():
    vals=row.dropna(); labels.append(MODULE_SHORT.get(module,module)); pos.append(int((vals>0).sum())); neg.append(int((vals<0).sum()))
y=np.arange(len(labels)); ax.barh(y,pos,color=COLORS['mouse']); ax.barh(y,neg,left=pos,color=COLORS['human'])
ax.set_yticks(y); ax.set_yticklabels(labels,fontsize=5.2); ax.set_xlabel('Contrasts',fontsize=6); ax.set_xlim(0,7)
ax.set_title('E. Direction consistency',fontsize=6.8,fontweight='bold',loc='left'); ax.spines[['top','right']].set_visible(False)
fig.suptitle('Independent human heart failure and cardiomyopathy evidence',fontsize=10.5,fontweight='bold')
fig.text(0.5,-0.02,'D: circle colour and size show effect direction/magnitude; edge: black FDR<0.05, dark grey FDR<0.10, light grey nominal p<0.05.',ha='center',fontsize=5.2,color=COLORS['muted'])
save_figure(fig,FIG/'PlanB_Figure3_HumanEvidence_v2',alignment_exclude_axes=[cax]); print('wrote',FIG/'PlanB_Figure3_HumanEvidence_v2.pdf')

