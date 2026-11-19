# -*- coding: utf-8 -*-
"""Plan B Figure 4 v2: spatial programme architecture with tissue overlays."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
import sys, gzip, json
from pathlib import Path
import numpy as np, pandas as pd
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_figure_style_v2 import *
DATA=ROOT/'02_unpacked'/'GSE297745'; samples={'GSM8998316':('ICI','WO_66093'),'GSM8998317':('ICI','WO_66094'),'GSM8998318':('Rescue','WO_66095'),'GSM8998319':('Rescue','WO_66096')}
spots=pd.read_csv(OUT/'gse297745_controlscore_spots.csv.gz'); niche=pd.read_csv(OUT/'gse297745_spatial_niche.csv')
mods=['Fibrosis_ECM','Inflammation','Endothelial','Hypoxia_Metabolism','CM_stress','Tcell_cytotoxic']
fig=plt.figure(figsize=(7.4,6.4)); gs=fig.add_gridspec(2,4,height_ratios=[1.05,0.92],hspace=0.24,wspace=0.16)
map_axes=[fig.add_subplot(gs[0,i]) for i in range(4)]; vmin,vmax=np.percentile(spots['Fibrosis_ECM'].dropna(),[2,98])
for ax,(gsm,(group,suf)) in zip(map_axes,samples.items()):
    with gzip.open(DATA/f'{gsm}_{suf}_tissue_hires_image.png.gz','rb') as f: img=Image.open(f).convert('RGB')
    with gzip.open(DATA/f'{gsm}_{suf}_scalefactors_json.json.gz','rt') as f: sf=json.load(f)['tissue_hires_scalef']
    pos=pd.read_csv(DATA/f'{gsm}_{suf}_tissue_positions.csv.gz').rename(columns={'barcode':'spot'}); d=spots[spots.GSM==gsm].merge(pos,on='spot')
    ax.imshow(img); ax.scatter(d.pxl_col_in_fullres*sf,d.pxl_row_in_fullres*sf,c=d.Fibrosis_ECM,s=3.2,cmap='RdBu_r',vmin=vmin,vmax=vmax,linewidths=0,alpha=.78)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(f'{group}\n{gsm[-4:]}',fontsize=6,fontweight='bold')
    for s in ax.spines.values(): s.set_visible(False)
map_axes[0].text(-0.08,1.09,'A',transform=map_axes[0].transAxes,fontsize=9,fontweight='bold')
cax=fig.add_axes([0.92,0.56,0.012,0.30]); cb=fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(vmin,vmax),cmap='RdBu_r'),cax=cax); cb.set_label('Fibrosis-ECM score',fontsize=6); cb.ax.tick_params(labelsize=5.5,length=1.5)
pairs=niche[niche.Module.str.contains('->',regex=False)].copy(); pairs[['Source','Target']]=pairs.Module.str.split('->',expand=True)
short_list=['Fibrosis_ECM','Inflammation','Hypoxia_Metabolism','CM_stress','Tcell_cytotoxic']; short_labels=[str(i) for i in range(1,6)]
heat_axes=[fig.add_subplot(gs[1,0]),fig.add_subplot(gs[1,1])]
for ax,group,label in zip(heat_axes,['ICI','Rescue'],['B','C']):
    d=pairs[pairs.Group==group]; mat=np.full((5,5),np.nan)
    for i,src in enumerate(short_list):
        for j,tgt in enumerate(short_list):
            r=d[(d.Source==src)&(d.Target==tgt)].Enrichment
            if len(r): mat[i,j]=r.mean()
    ann=np.where(np.isfinite(mat),np.vectorize(lambda x:f'{x:.2f}')(np.nan_to_num(mat)),'')
    im=heatmap(ax,mat,short_labels,short_labels,title=f'{label}. {group}: source to target',annotations=None,vmin=-.45,vmax=.45,fontsize=5.2)
    ax.tick_params(axis='x',rotation=45)
ax=fig.add_subplot(gs[1,2:]); mor=niche[~niche.Module.str.contains('->',regex=False)].groupby(['Module','Group']).Morans_I.mean().unstack(); ys=np.arange(len(mods))
for m,y in zip(mods,ys): ax.plot([mor.loc[m,'ICI'],mor.loc[m,'Rescue']],[y,y],color=COLORS['grid'],lw=1.0,zorder=1)
ax.scatter(mor.loc[mods,'ICI'],ys,color=COLORS['mouse'],s=22,label='ICI',zorder=3); ax.scatter(mor.loc[mods,'Rescue'],ys,color=COLORS['human'],s=22,label='Rescue',zorder=3)
ax.set_yticks(ys); ax.set_yticklabels([str(i) for i in range(1,7)],fontsize=5.5); ax.set_xlim(0,1); ax.set_xlabel("Moran's I",fontsize=6); ax.set_title('D. Spatial autocorrelation',fontsize=6.7,fontweight='bold',loc='left'); ax.legend(fontsize=5.2,frameon=False,loc='lower right'); ax.spines[['top','right']].set_visible(False)
fig.suptitle('Spatial programme architecture in mouse ICI myocarditis',fontsize=10.5,fontweight='bold')
fig.subplots_adjust(bottom=0.09)
fig.text(0.5,0.045,'B/C key: 1 Fibrosis-ECM; 2 Inflammation; 3 Hypoxia; 4 CM stress; 5 Cytotoxic T.',ha='center',va='center',fontsize=6.4,color=COLORS['muted'])
fig.text(0.5,0.018,'D key: 1 Fibrosis-ECM; 2 Inflammation; 3 Endothelial; 4 Hypoxia; 5 CM stress; 6 Cytotoxic T.',ha='center',va='center',fontsize=6.4,color=COLORS['muted'])
save_figure(fig,FIG/'PlanB_Figure4_Spatial_v2',alignment_exclude_axes=[cax]); print('wrote',FIG/'PlanB_Figure4_Spatial_v2.pdf')

