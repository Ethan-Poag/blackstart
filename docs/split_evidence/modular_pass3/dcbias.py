"""Typical Samsung DC-bias curves (deltaC % vs Vdc, 25 C, 1 kHz) extracted from the public product pages
(product.samsungsem.com/mlcc/<part>.do, 'datasheetData' JSON, graphType DCBias) into dcbias_curves.json.
Run: python3 dcbias.py > dcbias.txt"""
import json
C=json.load(open('dcbias_curves.json'))
def at(c,v):
    for (x1,y1),(x2,y2) in zip(c,c[1:]):
        if x1<=v<=x2: return y1+(y2-y1)*(v-x1)/(x2-x1) if x2>x1 else y1
for mpn,vs in (('CL21B105KBFNNNE',(9.27,11.0,12.83)),('CL31B106KAHNNNE',(1.0,1.24,1.5,4.75)),('CL21B104KCFNNNE',(12.6,24,32,36))):
    print(mpn,', '.join('%.2f V: %+.1f %%'%(v,at(C[mpn]['points_V_pct'],v)) for v in vs))
