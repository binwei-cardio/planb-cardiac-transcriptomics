# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import urllib.parse, urllib.request, json, time, csv, re
import xml.etree.ElementTree as ET
ROOT = PLANB_ROOT
OUT=ROOT/'08_reports'; OUT.mkdir(parents=True,exist_ok=True)
BASE='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
HEAD={'User-Agent':'Mozilla/5.0','Accept-Encoding':'identity'}
QUERIES={
'HF_integrative':'("heart failure"[tiab] OR cardiomyopathy[tiab]) AND (single-cell[tiab] OR single cell[tiab] OR single-nucleus[tiab] OR single nucleus[tiab] OR scRNA[tiab] OR snRNA[tiab] OR "spatial transcriptomics"[tiab]) AND (integrative[tiab] OR cross-dataset[tiab] OR multi-dataset[tiab] OR harmonized[tiab] OR meta-analysis[tiab] OR "across datasets"[tiab])',
'cardiotox_singlecell':' (cardiotoxicity[tiab] OR cardiotoxic[tiab] OR cardiotoxicity[MeSH]) AND (single-cell[tiab] OR single cell[tiab] OR single-nucleus[tiab] OR single nucleus[tiab] OR scRNA[tiab] OR snRNA[tiab] OR spatial transcriptomics[tiab]) AND (doxorubicin[tiab] OR anthracycline[tiab] OR immune checkpoint[tiab] OR ICI[tiab])',
'HF_fibrosis_cytotoxic':' (heart failure[tiab] OR cardiomyopathy[tiab]) AND (fibrosis[tiab] OR fibroblast*[tiab] OR cytotoxic T[tiab] OR CD8[tiab]) AND (single-cell[tiab] OR single cell[tiab] OR single-nucleus[tiab] OR single nucleus[tiab] OR scRNA[tiab] OR snRNA[tiab] OR spatial transcriptomics[tiab])',
'doxorubicin_singlecell':' (doxorubicin[tiab] OR anthracycline[tiab]) AND (single-cell[tiab] OR single cell[tiab] OR single-nucleus[tiab] OR single nucleus[tiab] OR scRNA[tiab] OR snRNA[tiab] OR spatial transcriptomics[tiab])',
'ICI_myocarditis_singlecell':' ("immune checkpoint inhibitor"[tiab] OR "immune checkpoint inhibitors"[tiab] OR ICI[tiab]) AND (myocarditis[tiab] OR cardiotoxicity[tiab]) AND (single-cell[tiab] OR single cell[tiab] OR single-nucleus[tiab] OR single nucleus[tiab] OR scRNA[tiab] OR snRNA[tiab] OR spatial transcriptomics[tiab])'
}
def get(url):
    req=urllib.request.Request(url,headers=HEAD)
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()
def search(q):
    url=BASE+'esearch.fcgi?'+urllib.parse.urlencode({'db':'pubmed','term':q,'retmode':'json','retmax':40,'sort':'relevance'})
    return json.loads(get(url))['esearchresult'].get('idlist',[])
def fetch(ids):
    if not ids: return {}
    url=BASE+'efetch.fcgi?'+urllib.parse.urlencode({'db':'pubmed','id':','.join(ids),'retmode':'xml'})
    root=ET.fromstring(get(url)); out={}
    for art in root.findall('.//PubmedArticle'):
        pmid=art.findtext('.//PMID') or ''
        title=' '.join(''.join(art.find('.//ArticleTitle').itertext()).split()) if art.find('.//ArticleTitle') is not None else ''
        abstract=' '.join(' '.join(''.join(x.itertext()).split()) for x in art.findall('.//Abstract/AbstractText'))
        journal=art.findtext('.//Journal/Title') or ''
        year=art.findtext('.//JournalIssue/PubDate/Year') or art.findtext('.//JournalIssue/PubDate/MedlineDate') or ''
        doi=''
        for aid in art.findall('.//ArticleId'):
            if aid.attrib.get('IdType')=='doi': doi=aid.text or ''; break
        authors=[]
        for a in art.findall('.//AuthorList/Author')[:3]:
            fam=a.findtext('LastName') or ''; init=a.findtext('Initials') or ''
            if fam: authors.append((fam+' '+init).strip())
        out[pmid]={'PMID':pmid,'Title':title,'Journal':journal,'Year':year,'DOI':doi,'Authors':', '.join(authors),'Abstract':abstract}
    return out
allrows=[]; seen=set()
for label,q in QUERIES.items():
    ids=search(q); data=fetch(ids); print(label,'ids',len(ids),'fetched',len(data))
    for rank,pmid in enumerate(ids,1):
        if pmid not in data: continue
        row=data[pmid]; row['QuerySet']=label; row['QueryRank']=rank
        if pmid not in seen:
            seen.add(pmid); allrows.append(row)
    time.sleep(.4)
fields=['QuerySet','QueryRank','PMID','Title','Authors','Journal','Year','DOI','Abstract']
outcsv=OUT/'PlanB_related_literature_pubmed_20261118.csv'
with open(outcsv,'w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows([{k:r.get(k,'') for k in fields} for r in allrows])
print('wrote',outcsv,'rows',len(allrows))
# print compact top per query for manual screening
for label in QUERIES:
    print('\n###',label)
    sub=[r for r in allrows if r['QuerySet']==label][:25]
    for r in sub:
        print(f"{r['QueryRank']:02d}\t{r['PMID']}\t{r['Year']}\t{r['Title'][:180]}\t{r['DOI']}")
