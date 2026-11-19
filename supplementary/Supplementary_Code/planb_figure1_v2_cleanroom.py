# -*- coding: utf-8 -*-
"""Plan B Figure 1 v2: study design and evidence architecture."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from planb_figure_style_v2 import *
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig=plt.figure(figsize=(7.2,5.4),constrained_layout=True)
gs=fig.add_gridspec(2,2,wspace=0.16,hspace=0.18)
axA=fig.add_subplot(gs[0,0]); axB=fig.add_subplot(gs[0,1]); axC=fig.add_subplot(gs[1,0]); axD=fig.add_subplot(gs[1,1])
for ax in [axA,axB,axC,axD]:
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')

def box(ax,x,y,w,h,text,face,edge='#52616B',fs=5.8,bold=False,rounding=0.035):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0.012,rounding_size={rounding}',linewidth=0.7,edgecolor=edge,facecolor=face))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=fs,color=COLORS['ink'],fontweight='bold' if bold else 'normal',linespacing=1.25)

def arrow(ax,p1,p2,color=None):
    ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle='-|>',mutation_scale=8,lw=0.8,color=color or COLORS['ink'],shrinkA=0,shrinkB=0))

# A: clinical convergence
panel_label(axA,'A',x=-0.02,y=1.02); axA.text(0.05,0.96,'Clinical convergence',fontsize=8,fontweight='bold',va='top')
box(axA,0.04,0.58,0.40,0.22,'Heart failure\nheterogeneous aetiologies',COLORS['human_soft'])
box(axA,0.56,0.58,0.40,0.22,'Cancer therapy\nDox / ICI cardiotoxicity',COLORS['mouse_soft'])
box(axA,0.18,0.20,0.64,0.23,'Candidate shared programmes\nfibrosis  |  inflammation  |  cytotoxic T cells',COLORS['accent_soft'],bold=True)
arrow(axA,(0.24,0.57),(0.40,0.44)); arrow(axA,(0.76,0.57),(0.60,0.44))
axA.text(0.50,0.06,'The question is convergence, not a therapy-exclusive signature.',ha='center',fontsize=5.5,color=COLORS['muted'])

# B: dataset landscape
panel_label(axB,'B',x=-0.02,y=1.02); axB.text(0.05,0.96,'Dataset landscape',fontsize=8,fontweight='bold',va='top')
box(axB,0.04,0.62,0.92,0.20,'Human primary evidence\nGSE292067  |  GSE288222  |  GSE298023',COLORS['human_soft'])
box(axB,0.04,0.36,0.45,0.18,'Human sensitivity\nGSE161470  |  GSE135805',COLORS['neutral'])
box(axB,0.53,0.36,0.43,0.18,'Mouse spatial / scRNA\nGSE297745  |  GSE299032',COLORS['mouse_soft'])
box(axB,0.12,0.04,0.76,0.24,'499,147 cells or spots in integrated quantitative analysis',COLORS['accent_soft'],bold=True)
arrow(axB,(0.50,0.61),(0.50,0.55)); arrow(axB,(0.50,0.35),(0.50,0.26))

# C: pipeline
panel_label(axC,'C',x=-0.02,y=1.02); axC.text(0.05,0.96,'Harmonised analysis pipeline',fontsize=8,fontweight='bold',va='top')
steps=[('QC\ncounts / spots',COLORS['neutral']),('Lineage\nmarker scoring',COLORS['green_soft']),('Matched control-\ngene score',COLORS['human_soft']),('Sample-level\npseudobulk',COLORS['mouse_soft'])]
for i,(txt,c) in enumerate(steps):
    x=0.035+i*0.245
    box(axC,x,0.40,0.205,0.38,txt,c,fs=5.3)
    if i<3: arrow(axC,(x+0.205,0.59),(x+0.245,0.59))
box(axC,0.04,0.06,0.92,0.24,'Seven programmes:\nfibrosis-ECM; inflammation; endothelial;\nhypoxia-metabolism; CM stress; cytotoxic T; senescence',COLORS['accent_soft'],fs=5.0)

# D: evidence hierarchy
panel_label(axD,'D',x=-0.02,y=1.02); axD.text(0.05,0.96,'Evidence hierarchy and claim boundary',fontsize=8,fontweight='bold',va='top')
box(axD,0.05,0.62,0.42,0.21,'Primary human\n3 datasets',COLORS['human_soft'],bold=True)
box(axD,0.53,0.62,0.42,0.21,'Supportive mouse\nspatial / directional',COLORS['mouse_soft'],bold=True)
box(axD,0.08,0.31,0.84,0.19,'Cross-dataset direction\nnot a pooled effect-size meta-analysis',COLORS['neutral'])
box(axD,0.08,0.07,0.84,0.18,'Hypothesis-generating\nno causal or therapy-exclusive claim',COLORS['accent_soft'],bold=True)
arrow(axD,(0.26,0.61),(0.26,0.50)); arrow(axD,(0.74,0.61),(0.74,0.50)); arrow(axD,(0.50,0.30),(0.50,0.25))

fig.suptitle('Study design and evidence architecture',fontsize=11,fontweight='bold')
save_figure(fig,FIG/'PlanB_Figure1_StudyDesign_v2')
print('wrote',FIG/'PlanB_Figure1_StudyDesign_v2.pdf')


