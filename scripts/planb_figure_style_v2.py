# -*- coding: utf-8 -*-
"""Shared visual system for Plan B v2 figures."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

ROOT = PLANB_ROOT
FIG=ROOT/'04_figures'
OUT=ROOT/'03_output'
FIG.mkdir(exist_ok=True)

COLORS={
    'human':'#3E6FB0','mouse':'#C75B45','accent':'#D9A441',
    'ink':'#22313A','muted':'#65737E','grid':'#D9E0E5',
    'human_soft':'#DCE8F5','mouse_soft':'#F6DED8','accent_soft':'#F5E7B8',
    'neutral':'#EDF1F4','green':'#5D9C78','green_soft':'#DDEDE3',
}
GROUP_COLORS={'Donor':'#3E6FB0','DoxCM':'#C75B45','NICM':'#5D9C78','ND':'#3E6FB0','HF':'#C75B45','Control':'#3E6FB0','ICI':'#C75B45','Rescue':'#3E6FB0','ICI-model':'#C75B45'}
MODULES=['Fibrosis_ECM','Inflammation','Endothelial','Hypoxia_Metabolism','CM_stress','Tcell_cytotoxic','Senescence']
MODULE_SHORT={'Fibrosis_ECM':'Fibrosis','Inflammation':'Inflam.','Endothelial':'Endo.','Hypoxia_Metabolism':'Hypoxia','CM_stress':'CM stress','Tcell_cytotoxic':'Cytotoxic T','Senescence':'Senescence'}
CELLTYPES=['Cardiomyocytes','Fibroblasts','Myeloid','T_NK','Endothelial','Pericyte_SMC']

plt.rcParams.update({
    'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans','sans-serif'],
    'font.size':7,'axes.titlesize':7.5,'axes.labelsize':7,
    'xtick.labelsize':6,'ytick.labelsize':6,'legend.fontsize':6,
    'axes.spines.right':False,'axes.spines.top':False,'axes.linewidth':0.8,
    'pdf.fonttype':42,'svg.fonttype':'none','figure.facecolor':'white','axes.facecolor':'white',
})

def panel_label(ax,label,x=-0.08,y=1.08,size=9):
    ax.text(x,y,label,transform=ax.transAxes,fontsize=size,fontweight='bold',va='top',ha='left')

def save_figure(fig,stem,dpi=600,transparent=False,alignment_exemptions=(),alignment_exclude_axes=()):
    stem=Path(stem)
    base=stem.parent
    name=stem.stem
    qa_dir=base/'qa'
    qa_dir.mkdir(parents=True,exist_ok=True)
    skill_scripts=Path(os.environ.get('NATURE_FIGURE_SCRIPTS', str(Path.home()/'.codex'/'skills'/'nature-figure'/'scripts')))
    if str(skill_scripts) not in sys.path:
        sys.path.insert(0,str(skill_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    require_matplotlib_panel_alignment(
        fig,
        json_out=qa_dir/(name+'.alignment.json'),
        overlay_svg=qa_dir/(name+'.alignment.svg'),
        exemptions=alignment_exemptions,
        exclude_axes=alignment_exclude_axes,
    )
    for suffix in ['.png','.pdf','.svg','.tiff']:
        outdir=base/suffix.lstrip('.')
        outdir.mkdir(parents=True,exist_ok=True)
        kwargs={'bbox_inches':'tight','transparent':transparent}
        if suffix=='.png': kwargs['dpi']=dpi
        if suffix=='.tiff': kwargs.update({'dpi':dpi,'pil_kwargs':{'compression':'tiff_lzw'}})
        fig.savefig(outdir/(name+suffix),**kwargs)
    plt.close(fig)

def heatmap(ax,values,row_labels,col_labels,title='',annotations=None,vmin=-1.0,vmax=1.0,cmap='RdBu_r',fontsize=5.5):
    import numpy as np
    norm=TwoSlopeNorm(vmin=vmin,vcenter=0,vmax=vmax)
    im=ax.imshow(values,cmap=cmap,norm=norm,aspect='auto')
    ax.set_xticks(range(len(col_labels))); ax.set_xticklabels(col_labels,rotation=50,ha='right',fontsize=fontsize)
    ax.set_yticks(range(len(row_labels))); ax.set_yticklabels(row_labels,fontsize=fontsize)
    ax.set_title(title,fontsize=7,fontweight='bold',loc='left')
    for s in ax.spines.values(): s.set_visible(False)
    if annotations is not None:
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                if annotations[i][j]:
                    ax.text(j,i,annotations[i][j],ha='center',va='center',fontsize=fontsize,color=COLORS['ink'])
    return im

