# -*- coding: utf-8 -*-
"""Post-process GSE298023 cell-level module scores: cell-type-stratified pseudobulk + heatmaps."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = str(PLANB_ROOT)
OUT=os.path.join(ROOT,"03_output"); FIG=os.path.join(ROOT,"04_figures","png")
MODULES=["Fibrosis_ECM","Inflammation","Endothelial","Hypoxia_Metabolism","CM_stress","Tcell_cytotoxic"]
df=pd.read_csv(os.path.join(OUT,"gse298023_cell_module_scores.csv.gz"))
print("cells:",len(df),"| celltypes:",df.celltype.nunique(),"| groups:",df.Group.unique())
# pseudobulk: mean per sample x celltype
pb=df.groupby(["GSM","Group","celltype"])[MODULES].mean().reset_index()
pb.to_csv(os.path.join(OUT,"gse298023_pseudobulk_celltype.csv"),index=False)
# group-level means per celltype
grp=pb.groupby(["celltype","Group"])[MODULES].agg(["mean","std","count"])
grp.columns=["_".join(c) for c in grp.columns]
grp=grp.reset_index()
grp.to_csv(os.path.join(OUT,"gse298023_celltype_group_summary.csv"),index=False)
order=["Cardiomyocytes","Fibroblasts","Myeloid","T_NK","Endothelial","Pericyte_SMC"]
present=[c for c in order if c in set(pb.celltype)]
# heatmap: HF - Donor differences (ICM and DCM)
for grpname in ["ICM","DCM"]:
    diff=[]
    for ct in present:
        row=[]
        for mod in MODULES:
            d=pb[(pb.celltype==ct)&(pb.Group=="Donor")][mod]
            h=pb[(pb.celltype==ct)&(pb.Group==grpname)][mod]
            row.append(float(h.mean()-d.mean()) if len(d) and len(h) else np.nan)
        diff.append(row)
    arr=np.array(diff)
    fig,ax=plt.subplots(figsize=(10,4))
    im=ax.imshow(arr,cmap="RdBu_r",vmin=-0.6,vmax=0.6)
    ax.set_xticks(range(len(MODULES))); ax.set_xticklabels(MODULES,rotation=45,ha="right",fontsize=9)
    ax.set_yticks(range(len(present))); ax.set_yticklabels(present,fontsize=9)
    ax.set_title(f"{grpname} - Donor (cell-type pseudobulk, module score difference)")
    plt.colorbar(im,ax=ax,fraction=0.03)
    plt.tight_layout(); plt.savefig(os.path.join(FIG,f"GSE298023_{grpname}_vs_Donor_heatmap.png"),dpi=300); plt.close()
    print("\n",grpname,"vs Donor (cell-type pseudobulk differences):")
    print(pd.DataFrame(arr,index=present,columns=MODULES).round(3).to_string())
print("\nDONE")
