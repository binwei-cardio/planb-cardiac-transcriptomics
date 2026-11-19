# -*- coding: utf-8 -*-
"""GSE292067: human heart snRNA - Donor (8) vs DoxCM (11) vs NICM (6).
Control-gene module scores + cell-type stratification + permutation tests.
"""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os, sys, glob, gzip, itertools
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from planb_ucell_lib import load_mtx_dir
from planb_controlscore_lib import control_module_scores
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = str(PLANB_ROOT); D=ROOT+r"\02_unpacked\GSE292067_pyfresh_20261115"; OUT=ROOT+r"\03_output"; FIG=ROOT+r"\04_figures\png"
GROUPS={
 "Donor":[f"GSM8848{n}" for n in range(306,314)],
 "DoxCM":[f"GSM8848{n}" for n in range(314,325)],
 "NICM":[f"GSM8848{n}" for n in range(325,331)],
}
MODULES={
 "Fibrosis_ECM":["COL1A1","COL1A2","COL3A1","COL5A1","COL8A1","FN1","POSTN","FAP","TGFB1","TGFBR1","ACTA2","TIMP1","LOX","COMP","THBS1","LUM","DCN"],
 "Inflammation":["IL6","IL1B","TNF","CCL2","CCR2","CXCL10","IFNG","STAT1","NFKB1","NLRP3","CD68","LYZ","ITGAM","TLR4","CCL5","IL10"],
 "Endothelial":["PECAM1","VWF","CDH5","KDR","FLT1","ANGPT2","VEGFA","ESM1","ENG","NOS3"],
 "Hypoxia_Metabolism":["HIF1A","VEGFA","SLC2A1","LDHA","PGK1","ENO1","HK2","PDK1","BNIP3","NDRG1","ANGPTL4"],
 "CM_stress":["NPPA","NPPB","MYH7","ACTC1","TNNT2","TTN","MYL2","PLN","MYH6"],
 "Tcell_cytotoxic":["CD3E","CD3D","CD8A","NKG7","GZMB","PRF1","IFNG","CCL5"],
 "Senescence":["CDKN1A","CDKN2A","TP53","GLB1","SERPINE1","IL6","CXCL8","LMNB1"],
}
MARKERS={
 "Cardiomyocytes":["MYH6","MYH7","NPPA","NPPB","ACTC1","TNNT2","TTN"],
 "Fibroblasts":["COL1A1","COL1A2","DCN","POSTN","LUM","PDGFRA","COL3A1"],
 "Myeloid":["CD68","LYZ","ITGAM","CCR2","CD14","FCGR1A"],
 "T_NK":["CD3E","CD3D","CD8A","CD4","NKG7","GZMB","PRF1"],
 "Endothelial":["PECAM1","CDH5","VWF","KDR","FLT1"],
 "Pericyte_SMC":["RGS5","PDGFRB","ACTA2","MYH11","DES"],
}
def files_for(gsm):
    m=glob.glob(os.path.join(D,gsm+"*_matrix.mtx.gz"))
    if not m: return None
    return m[0][:-len("_matrix.mtx.gz")]
def perm(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float); obs=abs(a.mean()-b.mean()); pool=np.concatenate([a,b]); n=len(a); c=t=0
    for comb in itertools.combinations(range(len(pool)),n):
        s=set(comb); g1=[pool[i] for i in s]; g2=[pool[i] for i in range(len(pool)) if i not in s]
        if abs(np.mean(g1)-np.mean(g2))>=obs-1e-12: c+=1
        t+=1
    return obs,(c/t if t else np.nan)
def bh(p):
    p=np.asarray(p,float); order=np.argsort(p); ranked=p[order]*len(p)/np.arange(1,len(p)+1)
    ranked=np.minimum.accumulate(ranked[::-1])[::-1]; out=np.empty(len(p)); out[order]=np.clip(ranked,0,1); return out
allrows=[]; pbs=[]
for grp,gsms in GROUPS.items():
    for gsm in gsms:
        base=files_for(gsm)
        if not base: print("missing",gsm); continue
        X,syms,bcs=load_mtx_dir(base)
        sc,ctrl=control_module_scores(X,syms,MODULES,n_ctrl=10,n_bins=20,seed=42)
        # marker-based cell type
        mk={}
        sym2idx={s.upper():i for i,s in enumerate(syms)}
        totals=np.asarray(X.sum(axis=1)).ravel()
        for ct,genes in MARKERS.items():
            cols=[sym2idx[g] for g in genes if g in sym2idx]
            mk[ct]=np.asarray(X[:,cols].todense()).mean(axis=1) if cols else np.zeros(X.shape[0])
        mkdf=pd.DataFrame(mk); ct=mkdf.idxmax(axis=1)
        d=pd.DataFrame({"GSM":gsm,"Group":grp,"cell":bcs,"n_counts":totals}); d=d.join(sc); d["celltype"]=ct.values
        d=d[d.n_counts>=200]
        allrows.append(d); pbs.append({"GSM":gsm,"Group":grp,**{m:float(np.nanmean(sc[m][(np.asarray(X.sum(axis=1)).ravel()>=200)])) for m in MODULES}})
        print(gsm,grp,"cells(kept):",len(d))
big=pd.concat(allrows,ignore_index=True); big.to_csv(OUT+r"\gse292067_cell_module_scores.csv.gz",index=False,compression="gzip")
pb=pd.DataFrame(pbs); pb.to_csv(OUT+r"\gse292067_pseudobulk_sample.csv",index=False)
pbc=big.groupby(["GSM","Group","celltype"])[list(MODULES.keys())].mean().reset_index()
pbc.to_csv(OUT+r"\gse292067_pseudobulk_celltype.csv",index=False)
res=[]
for ct in sorted(pbc.celltype.unique()):
    for m in MODULES:
        for g1,g2,label in [("DoxCM","Donor","DoxCM_vs_Donor"),("NICM","Donor","NICM_vs_Donor"),("DoxCM","NICM","DoxCM_vs_NICM")]:
            a=pbc[(pbc.celltype==ct)&(pbc.Group==g1)][m].values; b=pbc[(pbc.celltype==ct)&(pbc.Group==g2)][m].values
            if len(a)<3 or len(b)<3: continue
            diff,p=perm(a,b)
            res.append({"CellType":ct,"Comparison":label,"Module":m,"n1":len(a),"n2":len(b),
                        "mean1":round(float(a.mean()),3),"mean2":round(float(b.mean()),3),"diff":round(float(a.mean()-b.mean()),3),"perm_p":round(float(p),4)})
R=pd.DataFrame(res); R["FDR"]=np.nan
for label,g in R.groupby("Comparison"):
    R.loc[g.index,"FDR"]=bh(g.perm_p.values).round(4)
R.to_csv(OUT+r"\gse292067_celltype_permutation.csv",index=False)
print(pb.round(3).to_string(index=False))
key=R[(R.Comparison=="DoxCM_vs_Donor")&(R.Module.isin(["Fibrosis_ECM","CM_stress","Tcell_cytotoxic","Inflammation","Senescence"]))]
print(key.sort_values("perm_p").head(15).to_string(index=False))
# heatmap DoxCM vs Donor
piv=R[R.Comparison=="DoxCM_vs_Donor"].pivot(index="CellType",columns="Module",values="diff")
fig,ax=plt.subplots(figsize=(11,4.5))
im=ax.imshow(piv.values,cmap="RdBu_r",vmin=-0.5,vmax=0.5)
ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels(piv.columns,rotation=30,ha="right",fontsize=9)
ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index,fontsize=9)
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        pv=R[(R.Comparison=="DoxCM_vs_Donor")&(R.CellType==piv.index[i])&(R.Module==piv.columns[j])]["perm_p"].values
        mark="*" if len(pv) and pv[0]<0.05 else ""
        ax.text(j,i,f"{piv.values[i,j]:.2f}{mark}",ha="center",va="center",fontsize=8)
plt.colorbar(im,ax=ax,fraction=0.03,label="DoxCM - Donor (module score)")
ax.set_title("GSE292067: DoxCM vs Donor, cell-type stratified")
plt.tight_layout(); plt.savefig(FIG+r"\GSE292067_DoxCM_vs_Donor_heatmap.png",dpi=300); plt.close()
print("DONE")

