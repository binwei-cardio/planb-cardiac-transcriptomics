# -*- coding: utf-8 -*-
"""Plan B pilot-5: GSE298023 human LV snRNA (ICM vs DCM vs non-failing donor), memory-efficient."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os, sys, glob, gzip
import numpy as np, pandas as pd
import scipy.io, scipy.sparse as sp
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu, kruskal

ROOT = str(PLANB_ROOT)
D=os.path.join(ROOT,"02_unpacked","GSE298023"); OUT=os.path.join(ROOT,"03_output"); FIG=os.path.join(ROOT,"04_figures","png"); FIG_SVG=os.path.join(ROOT,"04_figures","svg")
os.makedirs(OUT,exist_ok=True); os.makedirs(FIG,exist_ok=True); os.makedirs(FIG_SVG,exist_ok=True)

GROUPS={
 "ICM":["GSM9004761","GSM9004763","GSM9004765","GSM9004769","GSM9004770"],
 "DCM":["GSM9004766","GSM9004767","GSM9004771","GSM9004772","GSM9004773","GSM9004778"],
 "Donor":["GSM9004774","GSM9004775"],
}
MODULES={
 "Fibrosis_ECM":["COL1A1","COL1A2","COL3A1","COL5A1","COL8A1","FN1","POSTN","FAP","TGFB1","TGFBR1","ACTA2","TIMP1","LOX","COMP","THBS1","LUM","DCN"],
 "Inflammation":["IL6","IL1B","TNF","CCL2","CCR2","CXCL10","IFNG","STAT1","NFKB1","NLRP3","CD68","LYZ","ITGAM","TLR4","CCL5","IL10"],
 "Endothelial":["PECAM1","VWF","CDH5","KDR","FLT1","ANGPT2","VEGFA","ESM1","ENG","NOS3"],
 "Hypoxia_Metabolism":["HIF1A","VEGFA","SLC2A1","LDHA","PGK1","ENO1","HK2","PDK1","BNIP3","NDRG1","ANGPTL4"],
 "CM_stress":["NPPA","NPPB","MYH7","ACTC1","TNNT2","TTN","MYL2","PLN","MYH6"],
 "Tcell_cytotoxic":["CD3E","CD3D","CD8A","NKG7","GZMB","PRF1","IFNG","CCL5"],
}
MARKERS={
 "Cardiomyocytes":["MYH6","MYH7","NPPA","NPPB","ACTC1","TNNT2","TTN"],
 "Fibroblasts":["COL1A1","COL1A2","DCN","POSTN","LUM","PDGFRA","COL3A1"],
 "Myeloid":["CD68","LYZ","ITGAM","CCR2","CD14","FCGR1A"],
 "T_NK":["CD3E","CD3D","CD8A","CD4","NKG7","GZMB","PRF1"],
 "Endothelial":["PECAM1","CDH5","VWF","KDR","FLT1"],
 "Pericyte_SMC":["RGS5","PDGFRB","ACTA2","MYH11","DES"],
}
ALL=sorted({g for v in list(MODULES.values())+list(MARKERS.values()) for g in v})

def files_for(gsm):
    m=glob.glob(os.path.join(D, gsm+"*_matrix.mtx.gz"))
    if not m: return None
    base=m[0][:-len("_matrix.mtx.gz")]
    return base+"_matrix.mtx.gz", base+"_features.tsv.gz", base+"_barcodes.tsv.gz"

def load_sample(gsm, genes):
    fs=files_for(gsm)
    if not fs: return None
    mtx,feat,bc=fs
    X=sp.csr_matrix(scipy.io.mmread(mtx)).T  # cells x genes
    symbols=[]
    with gzip.open(feat,"rt",encoding="utf-8") as f:
        for line in f:
            p=line.rstrip("\n").split("\t")
            symbols.append(p[1] if len(p)>1 else p[0])
    sym2idx={s.upper():i for i,s in enumerate(symbols)}
    cols=[sym2idx[g.upper()] for g in genes if g.upper() in sym2idx]
    Xsel=X[:,cols].toarray().astype(np.float32)
    totals=np.asarray(X.sum(axis=1)).ravel().astype(np.float64)
    barcodes=[l.strip().split("\t")[0] for l in gzip.open(bc,"rt",encoding="utf-8")]
    return Xsel, totals, barcodes

def main():
    mats=[]; tots=[]; meta=[]
    for grp,gsms in GROUPS.items():
        for gsm in gsms:
            r=load_sample(gsm, ALL)
            if r is None: print("missing",gsm); continue
            Xsel,totals,barcodes=r
            keep=totals>=200  # QC
            mats.append(Xsel[keep]); tots.append(totals[keep])
            meta += [(gsm,grp,b) for b,k in zip(barcodes,keep) if k]
            print(gsm,grp,"cells(kept):",int(keep.sum()))
    X=np.vstack(mats); totals=np.concatenate(tots)
    cpm=X/totals[:,None]*1e6; logx=np.log1p(cpm)
    z=(logx-logx.mean(axis=0,keepdims=True))/(logx.std(axis=0,keepdims=True)+1e-9)
    idx={g:i for i,g in enumerate(ALL)}
    sc={}
    for mod,genes in MODULES.items():
        cols=[idx[g] for g in genes if g in idx]
        sc[mod]=z[:,cols].mean(axis=1) if len(cols)>=3 else np.full(z.shape[0],np.nan)
    mk={}
    for ct,genes in MARKERS.items():
        cols=[idx[g] for g in genes if g in idx]
        mk[ct]=z[:,cols].mean(axis=1) if len(cols)>=3 else np.full(z.shape[0],np.nan)
    mkd=pd.DataFrame(mk); ct=mkd.idxmax(axis=1).where(mkd.max(axis=1)>0,"Unassigned")
    df=pd.DataFrame({"GSM":[m[0] for m in meta],"Group":[m[1] for m in meta],"cell":[m[2] for m in meta],"n_counts":totals})
    for k,v in sc.items(): df[k]=v
    df["celltype"]=ct.values
    df.to_csv(os.path.join(OUT,"gse298023_cell_module_scores.csv.gz"),index=False,compression="gzip")
    # pseudobulk per sample
    pb=df.groupby(["GSM","Group"])[list(MODULES.keys())].mean().reset_index()
    pb.to_csv(os.path.join(OUT,"gse298023_pseudobulk_sample_scores.csv"),index=False)
    # group summary (cell-level and sample-level)
    rows=[]
    for mod in MODULES:
        for grp in ["Donor","ICM","DCM"]:
            v=df[df.Group==grp][mod].dropna()
            s=pb[pb.Group==grp][mod]
            rows.append({"Module":mod,"Group":grp,"n_cells":len(v),"cell_median":round(float(v.median()),3),
                         "n_samples":len(s),"sample_mean":round(float(s.mean()),3) if len(s) else np.nan})
    pd.DataFrame(rows).to_csv(os.path.join(OUT,"gse298023_summary.csv"),index=False)
    # cell type composition
    comp=df.groupby(["GSM","Group","celltype"]).size().unstack(fill_value=0)
    comp=(comp.T/comp.sum(axis=1)).T*100; comp.to_csv(os.path.join(OUT,"gse298023_celltype_composition.csv"))
    # figure: pseudobulk module scores by group
    fig,axes=plt.subplots(1,len(MODULES),figsize=(4*len(MODULES),4))
    for ax,mod in zip(axes,MODULES):
        d=[pb[pb.Group==g][mod] for g in ["Donor","ICM","DCM"]]
        ax.boxplot(d,tick_labels=["Donor","ICM","DCM"],showfliers=True); ax.set_title(mod,fontsize=10)
    plt.tight_layout(); plt.savefig(os.path.join(FIG,"GSE298023_pseudobulk_boxplots.png"),dpi=300); plt.savefig(os.path.join(FIG_SVG,"GSE298023_pseudobulk_boxplots.svg")); plt.close()
    print("DONE cells:",len(df)); print(pd.DataFrame(rows).to_string(index=False))
if __name__=="__main__":
    main()


