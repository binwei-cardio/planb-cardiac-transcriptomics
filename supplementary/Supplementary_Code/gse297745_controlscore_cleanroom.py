# -*- coding: utf-8 -*-
"""Apply control-gene module score to GSE297745 Visium."""
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os, sys, itertools
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from planb_ucell_lib import load_mtx_dir
from planb_controlscore_lib import control_module_scores
import sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PLANB_ROOT; D=ROOT/"02_unpacked"/"GSE297745"; OUT=ROOT/"03_output"
OUT.mkdir(parents=True,exist_ok=True)
SAMPLES={"GSM8998316":("ICI","WO_66093"),"GSM8998317":("ICI","WO_66094"),"GSM8998318":("Rescue","WO_66095"),"GSM8998319":("Rescue","WO_66096")}
MODULES={
 "Fibrosis_ECM":["Col1a1","Col1a2","Col3a1","Col5a1","Col8a1","Fn1","Postn","Fap","Tgfb1","Tgfbr1","Acta2","Timp1","Lox","Comp","Thbs1","Lum","Dcn"],
 "Inflammation":["Il6","Il1b","Tnf","Ccl2","Ccr2","Cxcl10","Ifng","Stat1","Nfkb1","Nlrp3","Cd68","Lyz2","Itgam","Tlr4","Ccl5","Il10"],
 "Endothelial":["Pecam1","Vwf","Cdh5","Kdr","Flt1","Angpt2","Vegfa","Esm1","Eng","Nos3"],
 "Hypoxia_Metabolism":["Hif1a","Vegfa","Slc2a1","Ldha","Pgk1","Eno1","Hk2","Pdk1","Bnip3","Ndrg1","Angptl4"],
 "CM_stress":["Nppa","Nppb","Myh7","Actc1","Tnnt2","Ttn","Myl2","Pln","Myh6"],
 "Tcell_cytotoxic":["Cd3e","Cd3d","Cd8a","Nkg7","Gzmb","Prf1","Ifng","Ccl5"],
}
def perm(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float); obs=abs(a.mean()-b.mean()); pool=np.concatenate([a,b]); n=len(a); c=t=0
    for comb in itertools.combinations(range(len(pool)),n):
        s=set(comb); g1=[pool[i] for i in s]; g2=[pool[i] for i in range(len(pool)) if i not in s]
        if abs(np.mean(g1)-np.mean(g2))>=obs-1e-12: c+=1
        t+=1
    return obs,c/t
allrows=[]; pbs=[]
for gsm,(grp,wo) in SAMPLES.items():
    X,syms,bcs=load_mtx_dir(os.path.join(D,f"{gsm}_{wo}"))
    sc,ctrl=control_module_scores(X,syms,MODULES,n_ctrl=10,n_bins=20,seed=42)
    totals=np.asarray(X.sum(axis=1)).ravel()
    d=pd.DataFrame({"GSM":gsm,"Group":grp,"spot":bcs,"n_counts":totals}); d=d.join(sc)
    d=d[d.n_counts>=50]
    allrows.append(d); pbs.append({"GSM":gsm,"Group":grp,**{m:float(sc.loc[d.index,m].mean()) for m in MODULES}})
    print(gsm,grp,"spots:",len(d))
big=pd.concat(allrows,ignore_index=True); big.to_csv(OUT/"gse297745_controlscore_spots.csv.gz",index=False,compression="gzip")
pb=pd.DataFrame(pbs); pb.to_csv(OUT/"gse297745_controlscore_pseudobulk.csv",index=False)
res=[]
for m in MODULES:
    a=pb[pb.Group=="ICI"][m]; b=pb[pb.Group=="Rescue"][m]
    diff,p=perm(a,b)
    res.append({"Dataset":"GSE297745","Module":m,"mean_ICI":round(a.mean(),4),"mean_Rescue":round(b.mean(),4),"diff":round(a.mean()-b.mean(),4),"perm_p":round(p,4)})
pd.DataFrame(res).to_csv(OUT/"gse297745_controlscore_permutation.csv",index=False)
print(pb.round(4).to_string(index=False)); print(pd.DataFrame(res).to_string(index=False))



