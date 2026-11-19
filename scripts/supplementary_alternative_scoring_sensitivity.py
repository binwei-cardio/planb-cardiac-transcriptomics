# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import glob, itertools, sys
import numpy as np, pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from planb_ucell_lib import load_mtx_dir, build_universe, ucell_scores
ROOT = PLANB_ROOT
DATA=ROOT/'02_unpacked'/'GSE292067_pyfresh_20261115'; OUT=ROOT/'03_output'; SUP=ROOT/'06_Manuscript'/'Supplementary_corrected_v2_20261118'
primary=pd.read_csv(OUT/'gse292067_cell_module_scores.csv.gz')
MODULES={'Fibrosis_ECM':['COL1A1','COL1A2','COL3A1','COL5A1','COL8A1','FN1','POSTN','FAP','TGFB1','TGFBR1','ACTA2','TIMP1','LOX','COMP','THBS1','LUM','DCN'],'Tcell_cytotoxic':['CD3E','CD3D','CD8A','NKG7','GZMB','PRF1','IFNG','CCL5'],'CM_stress':['NPPA','NPPB','MYH7','ACTC1','TNNT2','TTN','MYL2','PLN','MYH6'],'Senescence':['CDKN1A','CDKN2A','TP53','GLB1','SERPINE1','IL6','CXCL8','LMNB1']}
GROUPS={'DoxCM':sorted(primary.loc[primary.Group=='DoxCM','GSM'].unique()),'NICM':sorted(primary.loc[primary.Group=='NICM','GSM'].unique()),'Donor':sorted(primary.loc[primary.Group=='Donor','GSM'].unique())}
CELLTYPES=['Cardiomyocytes','Fibroblasts','Myeloid','T_NK','Endothelial','Pericyte_SMC']

def rank_scores_correct(X, syms, modules, universe_idx, universe_names, chunk=4000):
    N=len(universe_names); posmap={g:i for i,g in enumerate(universe_names)}; mod_cols={m:[posmap[g] for g in genes if g in posmap] for m,genes in modules.items()}; out={m:np.full(X.shape[0],np.nan,dtype=np.float32) for m in modules}
    for start in range(0,X.shape[0],chunk):
        end=min(start+chunk,X.shape[0]); dense=X[start:end][:,universe_idx].toarray().astype(np.float32); order=np.argsort(-dense,axis=1); ranks=np.empty_like(order,dtype=np.int32); np.put_along_axis(ranks,order,np.arange(1,dense.shape[1]+1,dtype=np.int32)[None,:],axis=1)
        for m,cols in mod_cols.items():
            if len(cols)<3: continue
            r=ranks[:,cols].astype(np.float64); U=r.sum(axis=1); n=len(cols); out[m][start:end]=np.clip(1.0-((U-n*(n+1)/2.0)/(n*N)),0,1).astype(np.float32)
    return pd.DataFrame(out)
def files_for(gsm):
    m=glob.glob(str(DATA/(gsm+'*_matrix.mtx.gz'))); return m[0][:-len('_matrix.mtx.gz')] if m else None
def bh(p):
    p=np.asarray(p,float); out=np.full(len(p),np.nan); ok=np.isfinite(p)
    if ok.any():
        q=p[ok]; order=np.argsort(q); ranked=q[order]*len(q)/np.arange(1,len(q)+1); ranked=np.minimum.accumulate(ranked[::-1])[::-1]; tmp=np.empty(len(q)); tmp[order]=np.clip(ranked,0,1); out[np.where(ok)[0]]=tmp
    return out
def perm(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float); obs=abs(a.mean()-b.mean()); pool=np.concatenate([a,b]); n=len(a); c=t=0
    for comb in itertools.combinations(range(len(pool)),n):
        s=set(comb); g1=[pool[i] for i in s]; g2=[pool[i] for i in range(len(pool)) if i not in s]
        if abs(np.mean(g1)-np.mean(g2))>=obs-1e-12: c+=1
        t+=1
    return obs,c/t
zrows=[]; rrows=[]
for group,gsms in GROUPS.items():
    for gsm in gsms:
        base=files_for(gsm)
        if not base: continue
        X,syms,bcs=load_mtx_dir(base); cmap={r.cell:r.celltype for r in primary[primary.GSM==gsm].itertuples()}; keep=np.array([b in cmap for b in bcs]); X=X[keep]; bcs=np.asarray(bcs)[keep]; cts=np.array([cmap[b] for b in bcs]); totals=np.asarray(X.sum(axis=1)).ravel().astype(float); sym2idx={s.upper():i for i,s in enumerate(syms)}
        for ct in CELLTYPES:
            mask=cts==ct
            if mask.sum()<3: continue
            for module,genes in MODULES.items():
                present=[g for g in genes if g in sym2idx]; cols=[sym2idx[g] for g in present]
                if len(cols)<3: continue
                M=np.asarray(X[mask][:,cols].todense(),float); ml=np.log1p(M/totals[mask,None]*1e6)
                for j,g in enumerate(present): zrows.append({'GSM':gsm,'Group':group,'CellType':ct,'Module':module,'Gene':g,'MeanLogCPM':float(ml[:,j].mean())})
        allgenes=sorted({g for genes in MODULES.values() for g in genes}); idx,names=build_universe(X,syms,allgenes,n_bg=1200,min_frac=0.03,seed=42); rsc=rank_scores_correct(X,syms,MODULES,idx,names,chunk=4000)
        for ct in CELLTYPES:
            mask=cts==ct
            if mask.sum()<3: continue
            for module in MODULES: rrows.append({'GSM':gsm,'Group':group,'CellType':ct,'Module':module,'RankScore':float(np.nanmean(rsc[module].values[mask]))})
        print(gsm,group,len(cts))
zraw=pd.DataFrame(zrows); rraw=pd.DataFrame(rrows); zscore=[]
for (ct,module,gene),g in zraw.groupby(['CellType','Module','Gene']):
    mu=g.MeanLogCPM.mean(); sd=g.MeanLogCPM.std(ddof=1)
    for r in g.itertuples(index=False): zscore.append({'GSM':r.GSM,'Group':r.Group,'CellType':ct,'Module':module,'GeneZ':(r.MeanLogCPM-mu)/sd if sd>0 else 0.0})
zpb=pd.DataFrame(zscore).groupby(['GSM','Group','CellType','Module'],as_index=False)['GeneZ'].mean(); zpb.to_csv(SUP/'Supplementary_Table_S5A_Zscore_pseudobulk.csv',index=False,encoding='utf-8-sig'); rraw.to_csv(SUP/'Supplementary_Table_S5B_Rank_score_pseudobulk.csv',index=False,encoding='utf-8-sig')
rows=[]
for method,df,valcol in [('Z-score',zpb,'GeneZ'),('Rank-based',rraw,'RankScore')]:
    for g1,g2,label in [('DoxCM','Donor','DoxCM_vs_Donor'),('NICM','Donor','NICM_vs_Donor'),('DoxCM','NICM','DoxCM_vs_NICM')]:
        comp=[]
        for ct in CELLTYPES:
            for module in MODULES:
                a=df[(df.Group==g1)&(df.CellType==ct)&(df.Module==module)][valcol].values; b=df[(df.Group==g2)&(df.CellType==ct)&(df.Module==module)][valcol].values
                if len(a)>=3 and len(b)>=3:
                    diff,p=perm(a,b); comp.append({'Method':method,'Comparison':label,'CellType':ct,'Module':module,'n1':len(a),'n2':len(b),'mean1':a.mean(),'mean2':b.mean(),'diff':diff,'p':p})
        if comp:
            c=pd.DataFrame(comp); c['FDR']=bh(c.p.values); rows.extend(c.to_dict('records'))
out=pd.DataFrame(rows); out.to_csv(SUP/'Supplementary_Table_S5_Alternative_scoring_tests.csv',index=False,encoding='utf-8-sig'); print('wrote',SUP/'Supplementary_Table_S5_Alternative_scoring_tests.csv','rows',len(out)); print(out.head(20).to_string(index=False))


