# -*- coding: utf-8 -*-
"""Plan B Figure 2 v2: DoxCM, NICM and donor programme landscape."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_figure_style_v2 import *
eff=pd.read_csv(OUT/'gse292067_contrast_effects_v2.csv'); pb=pd.read_csv(OUT/'gse292067_pseudobulk_celltype.csv')
mods=MODULES[:6]; ct_order=['Cardiomyocytes','Fibroblasts','Myeloid','T_NK','Endothelial','Pericyte_SMC']
contrasts=[('DoxCM_vs_Donor','DoxCM vs Donor'),('NICM_vs_Donor','NICM vs Donor'),('DoxCM_vs_NICM','DoxCM vs NICM')]
fig=plt.figure(figsize=(7.3,6.0)); gs=fig.add_gridspec(2,3,height_ratios=[1.0,0.95],left=0.07,right=0.90,bottom=0.08,top=0.90,hspace=0.35,wspace=0.28)
for k,(cmp,title) in enumerate(contrasts):
    ax=fig.add_subplot(gs[0,k]); sub=eff[eff.Comparison==cmp]
    mat=np.full((len(ct_order),len(mods)),np.nan); ann=np.full(mat.shape,'',dtype=object)
    for i,ct in enumerate(ct_order):
        for j,mod in enumerate(mods):
            r=sub[(sub.CellType==ct)&(sub.Module==mod)]
            if len(r):
                mat[i,j]=float(r['hedges_g'].iloc[0]); q=float(r['FDR'].iloc[0]); p=float(r['perm_p'].iloc[0])
                mark='**' if q<0.05 else ('*' if q<0.10 else ('†' if p<0.05 else '')); ann[i,j]=f"{mat[i,j]:.2f}{mark}"
    im=heatmap(ax,mat,[c.replace('_',' ') for c in ct_order],['Fibrosis','Inflam.','Endo.','Hypox.','CM','Cyto','Senes'],title=f"{'ABC'[k]}. {title}",annotations=ann,vmin=-1.2,vmax=1.2,fontsize=5.2)
    if k>0: ax.set_yticklabels([])
cax=fig.add_axes([0.92,0.58,0.012,0.31]); cb=fig.colorbar(im,cax=cax); cb.set_label("Hedges' g",fontsize=6); cb.ax.tick_params(labelsize=5.5,length=1.5)
pairs=[('Fibroblasts','Fibrosis_ECM','D. Fibroblast fibrosis-ECM'),('Cardiomyocytes','Senescence','E. Cardiomyocyte senescence'),('T_NK','Tcell_cytotoxic','F. T/NK cytotoxic')]; groups=['Donor','DoxCM','NICM']
for k,(ct,mod,title) in enumerate(pairs):
    ax=fig.add_subplot(gs[1,k]); sub=pb[(pb.celltype==ct)&(pb.Group.isin(groups))]; data=[sub[sub.Group==g][mod].dropna().values for g in groups]
    bp=ax.boxplot(data,patch_artist=True,widths=0.6,showfliers=False,medianprops={'color':'black','linewidth':1})
    for patch,g in zip(bp['boxes'],groups): patch.set_facecolor(GROUP_COLORS[g]); patch.set_alpha(0.45)
    rng=np.random.default_rng(10+k)
    for i,(g,vals) in enumerate(zip(groups,data),1): ax.scatter(np.full(len(vals),i)+rng.normal(0,0.04,len(vals)),vals,s=14,color=GROUP_COLORS[g],edgecolor='white',linewidth=0.3,zorder=3)
    ax.set_xticks([1,2,3]); ax.set_xticklabels(groups,fontsize=5.5); ax.axhline(0,color=COLORS['grid'],ls=':',lw=0.7)
    ax.set_title(title,fontsize=6.5,fontweight='bold',loc='left'); ax.set_ylabel('Module score',fontsize=6); ax.spines[['top','right']].set_visible(False)
fig.suptitle('DoxCM, NICM and donor programme landscape',fontsize=10.5,fontweight='bold')
fig.text(0.5,-0.02,'**FDR<0.05; *FDR<0.10; †nominal p<0.05. Direct DoxCM-vs-NICM contrasts did not survive FDR.',ha='center',fontsize=5.5,color=COLORS['muted'])
save_figure(fig,FIG/'PlanB_Figure2_DoxCM_NICM_v2',alignment_exclude_axes=[cax]); print('wrote',FIG/'PlanB_Figure2_DoxCM_NICM_v2.pdf')


