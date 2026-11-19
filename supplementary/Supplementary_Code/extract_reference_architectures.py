# -*- coding: utf-8 -*-
from planb_paths import PLANB_ROOT, PROJECT_ROOT
import os
from pathlib import Path
import urllib.parse, urllib.request, xml.etree.ElementTree as ET, sys, json
sys.stdout.reconfigure(encoding='utf-8')
OUT=PLANB_ROOT/'07_logs'/'reference_architectures_20261118'; OUT.mkdir(parents=True,exist_ok=True)
refs={
'Guo2025_Circulation':'12756910',
'Youness2025_GenomeMed':'12751894',
'Lee2025_EHJ':'12349961',
'Huang2026_BriefBioinform':'12874883',
'Blum2024_Nature':'12952943',
'Sun2025_JTM':'12084926',
'Bayer2024_NatCardiovascRes':'12324073'}
BASE='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
for name,pmcid in refs.items():
    url=BASE+'efetch.fcgi?'+urllib.parse.urlencode({'db':'pmc','id':pmcid,'retmode':'xml'})
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=120) as r: data=r.read()
    p=OUT/(name+'.xml'); p.write_bytes(data)
    root=ET.fromstring(data)
    print('\n===',name,'PMC',pmcid,'===')
    # abstract sections
    for ab in root.findall('.//abstract'):
        for sec in ab.findall('.//sec'):
            title=' '.join(''.join(sec.find('title').itertext()).split()) if sec.find('title') is not None else ''
            txt=' '.join(' '.join(''.join(x.itertext()).split()) for x in sec.findall('.//p'))
            if title or txt: print('ABSTRACT',title,'|',txt[:350])
    # top-level body sections and child headings
    body=root.find('.//body')
    if body is not None:
        for sec in body.findall('./sec'):
            title=' '.join(''.join(sec.find('title').itertext()).split()) if sec.find('title') is not None else ''
            print('SECTION',title)
            for sub in sec.findall('./sec'):
                st=' '.join(''.join(sub.find('title').itertext()).split()) if sub.find('title') is not None else ''
                if st: print('  SUB',st)
