# -*- coding: utf-8 -*-
"""Plan B: UCell-like rank-based module scoring (chunked, memory-safe)."""
import os, gzip, glob
import numpy as np, pandas as pd
import scipy.io, scipy.sparse as sp, h5py

def load_mtx_dir(base):
    X=sp.csc_matrix(scipy.io.mmread(base+"_matrix.mtx.gz")).T.tocsr()
    feats=pd.read_csv(base+"_features.tsv.gz",sep="\t",header=None)
    syms=feats[1].astype(str).str.upper().values
    bcs=pd.read_csv(base+"_barcodes.tsv.gz",sep="\t",header=None)[0].astype(str).values
    return X, syms, bcs

def load_h5(path):
    with h5py.File(path,"r") as f:
        g=f["matrix"]; shape=tuple(g["shape"][:])
        X=sp.csc_matrix((g["data"][:],g["indices"][:],g["indptr"][:]),shape=shape).T.tocsr()
        syms=np.array([x.decode() if isinstance(x,bytes) else str(x) for x in g["features"]["name"][:]]).astype(str)
        bcs=np.array([x.decode() if isinstance(x,bytes) else str(x) for x in g["barcodes"][:]]).astype(str)
    return X, syms, bcs

def build_universe(X, syms, module_genes, n_bg=1200, min_frac=0.03, seed=42):
    """module genes (present) + detection-filtered random background genes."""
    sym2idx={s.upper():i for i,s in enumerate(syms)}
    mod=[g.upper() for g in module_genes if g.upper() in sym2idx]
    det=np.asarray((X>0).sum(axis=0)).ravel()
    frac=det/max(X.shape[0],1)
    cand=[s.upper() for i,s in enumerate(syms) if frac[i]>=min_frac and s.upper() not in set(mod)]
    rng=np.random.default_rng(seed)
    bg=list(rng.choice(cand,size=min(n_bg,len(cand)),replace=False)) if cand else []
    universe=mod+[b for b in bg if b not in set(mod)]
    idx=[sym2idx[g] for g in universe if g in sym2idx]
    names=[g for g in universe if g in sym2idx]
    return idx, names

def ucell_scores(X, syms, modules, universe_idx, universe_names, chunk=4000, max_rank=None):
    """Returns DataFrame with UCell-like scores per cell (rows aligned to X)."""
    N=len(universe_names); posmap={g:i for i,g in enumerate(universe_names)}
    mod_cols={m:[posmap[g.upper()] for g in genes if g.upper() in posmap] for m,genes in modules.items()}
    out={m:np.full(X.shape[0],np.nan,dtype=np.float32) for m in modules}
    for start in range(0,X.shape[0],chunk):
        end=min(start+chunk,X.shape[0])
        dense=X[start:end][:,universe_idx].toarray().astype(np.float32)
        order=np.argsort(-dense,axis=1)                    # gene positions sorted by expression desc
        ranks=np.empty_like(order,dtype=np.int32)
        np.put_along_axis(ranks,np.arange(dense.shape[1])[None,:],np.arange(1,dense.shape[1]+1)[None,:],axis=1)
        ranks=np.take_along_axis(np.argsort(order,axis=1),np.argsort(np.argsort(order,axis=1)),axis=1)  # ensure ranks[pos]=rank
        for m,cols in mod_cols.items():
            if len(cols)<3: continue
            r=ranks[:,cols].astype(np.float64)
            U=r.sum(axis=1); n=len(cols)
            score=1.0-((U-n*(n+1)/2.0)/(n*N))
            out[m][start:end]=np.clip(score,0,1).astype(np.float32)
    return pd.DataFrame(out)
