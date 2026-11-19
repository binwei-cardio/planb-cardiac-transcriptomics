# -*- coding: utf-8 -*-
"""Control-gene module score (Seurat-like): mean(module) - mean(expression-matched controls)."""
import numpy as np, pandas as pd, scipy.sparse as sp

def control_module_scores(X, syms, modules, n_ctrl=10, n_bins=20, seed=42):
    """X: cells x genes sparse; syms: gene names (upper). Returns DataFrame of scores."""
    syms=np.array([str(s).upper() for s in syms])
    sym2idx={s:i for i,s in enumerate(syms)}
    mod_set={g.upper() for v in modules.values() for g in v}
    with np.errstate(invalid="ignore"):
        mean_expr=np.asarray(X.mean(axis=0)).ravel()
    # bin by mean expression
    order=np.argsort(mean_expr)
    bins=np.empty(len(syms),dtype=int)
    bins[order]=np.floor(np.linspace(0,n_bins-1,len(syms))).astype(int)
    rng=np.random.default_rng(seed)
    scores={}
    controls={}
    for mod,genes in modules.items():
        mod_idx=[sym2idx[g.upper()] for g in genes if g.upper() in sym2idx]
        ctrl_idx=[]
        for gi in mod_idx:
            b=bins[gi]
            cand=np.where((bins==b)&(~np.isin(np.arange(len(syms)),mod_idx)))[0]
            cand=[c for c in cand if c not in ctrl_idx]
            if len(cand)>0:
                pick=rng.choice(cand,size=min(n_ctrl,len(cand)),replace=False)
                ctrl_idx.extend(pick.tolist())
        ctrl_idx=list(dict.fromkeys(ctrl_idx))
        if len(mod_idx)<3: 
            scores[mod]=np.full(X.shape[0],np.nan); controls[mod]=[]; continue
        M=np.asarray(X[:,mod_idx].todense())
        C=np.asarray(X[:,ctrl_idx].todense()) if ctrl_idx else np.zeros((X.shape[0],1))
        totals=np.asarray(X.sum(axis=1)).ravel()
        Mlog=np.log1p(M/totals[:,None]*1e6); Clog=np.log1p(C/totals[:,None]*1e6)
        scores[mod]=Mlog.mean(axis=1)-Clog.mean(axis=1)
        controls[mod]=[syms[i] for i in ctrl_idx]
    return pd.DataFrame(scores), controls
