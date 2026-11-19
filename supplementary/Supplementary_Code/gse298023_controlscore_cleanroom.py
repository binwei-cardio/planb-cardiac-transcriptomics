# -*- coding: utf-8 -*-
"""Control-gene module scores for GSE298023 human LV snRNA (fixed expression-matched controls)."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os, sys, glob, gzip, itertools
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import scipy.io, scipy.sparse as sp
from planb_ucell_lib import load_mtx_dir
from planb_controlscore_lib import control_module_scores
ROOT = str(PLANB_ROOT); D=ROOT+r"\02_unpacked\GSE298023"; OUT=ROOT+r"\03_output"
GROUPS={"ICM":["GSM9004761","GSM9004763","GSM9004765","GSM9004769","GSM9004770"],
        "DCM":["GSM9004766","GSM9004767","GSM9004771","GSM9004772","GSM9004773","GSM9004778"],
        "Donor":["GSM9004774","GSM9004775"]}
MODULES={
 "Fibrosis_ECM":["COL1A1","COL1A2","COL3A1","COL5A1","COL8A1","FN1","POSTN","FAP","TGFB1","TGFBR1","ACTA2","TIMP1","LOX","COMP","THBS1","LUM","DCN"],
 "Inflammation":["IL6","IL1B","TNF","CCL2","CCR2","CXCL10","IFNG","STAT1","NFKB1","NLRP3","CD68","LYZ","ITGAM","TLR4","CCL5","IL10"],
 "Endothelial":["PECAM1","VWF","CDH5","KDR","FLT1","ANGPT2","VEGFA","ESM1","ENG","NOS3"],
 "Hypoxia_Metabolism":["HIF1A","VEGFA","SLC2A1","LDHA","PGK1","ENO1","HK2","PDK1","BNIP3","NDRG1","ANGPTL4"],
 "CM_stress":["NPPA","NPPB","MYH7","ACTC1","TNNT2","TTN","MYL2","PLN","MYH6"],
 "Tcell_cytotoxic":["CD3E","CD3D","CD8A","NKG7","GZMB","PRF1","IFNG","CCL5"],
}
def files_for(gsm):
    m=glob.glob(os.path.join(D,gsm+"*_matrix.mtx.gz"))
    if not m: return None
    base=m[0][:-len("_matrix.mtx.gz")]
    return base
def perm(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float); obs=abs(a.mean()-b.mean()); pool=np.concatenate([a,b]); n=len(a); c=t=0
    for comb in itertools.combinations(range(len(pool)),n):
        s=set(comb); g1=[pool[i] for i in s]; g2=[pool[i] for i in range(len(pool)) if i not in s]
        if abs(np.mean(g1)-np.mean(g2))>=obs-1e-12: c+=1
        t+=1
    return obs,c/t
# cell type labels from earlier run
ctdf=pd.read_csv(OUT+r"\gse298023_cell_module_scores.csv.gz")
ctmap={(r.GSM,r.cell):r.celltype for r in ctdf.itertuples()}
allrows=[]; pbs=[]
for grp,gsms in GROUPS.items():
    for gsm in gsms:
        base=files_for(gsm)
        if not base: print("missing",gsm); continue
        X,syms,bcs=load_mtx_dir(base)
        sc,ctrl=control_module_scores(X,syms,MODULES,n_ctrl=10,n_bins=20,seed=42)
        d=pd.DataFrame({"GSM":gsm,"Group":grp,"cell":bcs}); d=d.join(sc)
        d["celltype"]=[ctmap.get((gsm,c),"Unassigned") for c in bcs]
        allrows.append(d); pbs.append({"GSM":gsm,"Group":grp,**{m:float(sc[m].mean()) for m in MODULES}})
        print(gsm,grp,"cells:",len(d))
big=pd.concat(allrows,ignore_index=True); big.to_csv(OUT+r"\gse298023_controlscore_cells.csv.gz",index=False,compression="gzip")
pb=pd.DataFrame(pbs); pb.to_csv(OUT+r"\gse298023_controlscore_pseudobulk.csv",index=False)
# celltype-level pseudobulk
pbc=big.groupby(["GSM","Group","celltype"])[list(MODULES.keys())].mean().reset_index()
pbc.to_csv(OUT+r"\gse298023_controlscore_pseudobulk_celltype.csv",index=False)
res=[]
for ct in sorted(pbc.celltype.unique()):
    for m in MODULES:
        for g1,g2,label in [("ICM","Donor","ICM_vs_Donor"),("DCM","Donor","DCM_vs_Donor")]:
            a=pbc[(pbc.celltype==ct)&(pbc.Group==g1)][m].values
            b=pbc[(pbc.celltype==ct)&(pbc.Group==g2)][m].values
            if len(a)<2 or len(b)<2: continue
            diff,p=perm(a,b)
            res.append({"CellType":ct,"Comparison":label,"Module":m,"n1":len(a),"n2":len(b),
                        "mean1":round(float(a.mean()),4),"mean2":round(float(b.mean()),4),"diff":round(float(a.mean()-b.mean()),4),"perm_p":round(float(p),4)})
pd.DataFrame(res).to_csv(OUT+r"\gse298023_controlscore_celltype_permutation.csv",index=False)
print(pb.round(3).to_string(index=False))
df=pd.DataFrame(res)
key=df[(df.CellType.isin(["Fibroblasts","Cardiomyocytes","T_NK","Myeloid","Endothelial"]))&(df.Module.isin(["Fibrosis_ECM","CM_stress","Tcell_cytotoxic","Inflammation"]))]
print(key.to_string(index=False))


