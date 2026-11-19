# -*- coding: utf-8 -*-
"""Plan B Figure 5 v2: cross-dataset directional synthesis."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_figure_style_v2 import *
mat=pd.read_csv(OUT/'planb_cross_dataset_matrix_v4.csv',index_col=0); q=pd.read_csv(OUT/'planb_cross_dataset_qvalues_v4.csv',index_col=0)
mod_order=['Fibrosis_ECM','Tcell_cytotoxic','CM_stress','Inflammation','Senescence','Hypoxia_Metabolism']; mat=mat.reindex(mod_order); q=q.reindex(mod_order)
fig=plt.figure(figsize=(7.5,4.7),constrained_layout=True); gs=fig.add_gridspec(1,3,width_ratios=[2.1,0.85,0.85],wspace=0.35)
ax=fig.add_subplot(gs[0,0]); vals=mat.values; ann=np.full(vals.shape,'',dtype=object)
for i in range(vals.shape[0]):
    for j in range(vals.shape[1]):
        v=vals[i,j]; qq=q.values[i,j]
        if np.isfinite(v):
            mark='**' if np.isfinite(qq) and qq<.05 else ('*' if np.isfinite(qq) and qq<.10 else ('' if np.isfinite(qq) else 'd')); ann[i,j]=f'{v:.2f}{mark}'
im=heatmap(ax,vals,[MODULE_SHORT[m] for m in mod_order],["Dox vs D","NICM vs D","HF vs ND","ICM vs D","DCM vs D","ICI vs R","ICI vs C"],title='A. Programme-by-contrast effect matrix',annotations=ann,vmin=-0.8,vmax=0.8,fontsize=5.2); ax.set_xticklabels(["Dox vs D","NICM vs D","HF vs ND","ICM vs D","DCM vs D","ICI vs R","ICI vs C"],rotation=0,ha="center",fontsize=5.2)
cax=fig.add_axes([0.64,0.20,0.010,0.58]); cb=fig.colorbar(im,cax=cax); cb.set_label('')
cb.set_ticks([-0.8,0,0.8]); cb.ax.tick_params(length=0,pad=2); cb.ax.tick_params(labelsize=5.2,length=1.4)
ax=fig.add_subplot(gs[0,1]); labels=[]; pos=[]; neg=[]
for module in mod_order:
    x=mat.loc[module].dropna(); labels.append(MODULE_SHORT[module]); pos.append(int((x>0).sum())); neg.append(int((x<0).sum()))
y=np.arange(len(labels)); ax.barh(y,pos,color=COLORS['mouse'],label='Positive'); ax.barh(y,neg,left=pos,color=COLORS['human'],label='Negative')
ax.set_yticks(y); ax.set_yticklabels([]); ax.set_xlim(0,7); ax.set_xlabel('Contrasts',fontsize=5.8); ax.set_title('B. Direction count',fontsize=6.8,fontweight='bold',loc='left'); ax.spines[['top','right']].set_visible(False)
ax=fig.add_subplot(gs[0,2]); strong=[]; nominal=[]; ns=[]
for module in mod_order:
    vv=q.loc[module].dropna(); strong.append(int((vv<.05).sum())); nominal.append(int(((vv>=.05)&(vv<.10)).sum())); ns.append(int((vv>=.10).sum()))
y=np.arange(len(labels)); ax.barh(y,strong,color=COLORS['accent'],label='FDR<0.05'); ax.barh(y,nominal,left=strong,color=COLORS['green'],label='FDR<0.10'); ax.barh(y,ns,left=np.array(strong)+np.array(nominal),color=COLORS['neutral'],label='FDR>=0.10')
ax.set_yticks(y); ax.set_yticklabels([]); ax.set_xlabel('Tests',fontsize=5.8); ax.set_title('C. Evidence strength',fontsize=6.8,fontweight='bold',loc='left'); ax.spines[['top','right']].set_visible(False)
fig.suptitle('Cross-dataset directional synthesis',fontsize=10.5,fontweight='bold')
fig.text(0.5,-0.02,'Colour scale: disease/cardiotoxicity minus control. B: rust = positive, blue = negative. C: gold = FDR<0.05, green = FDR<0.10, grey = remaining. **FDR<0.05; *FDR<0.10; d = directional only.',ha='center',fontsize=5.3,color=COLORS['muted'])
save_figure(fig,FIG/'PlanB_Figure5_CrossDataset_v2',alignment_exemptions=[{'panels':['a','b','c'],'checks':['panel-width'],'reason':'Panel A is intentionally wider than panels B and C to accommodate the seven-contrast heatmap.'}],alignment_exclude_axes=[cax]); print('wrote',FIG/'PlanB_Figure5_CrossDataset_v2.pdf')



