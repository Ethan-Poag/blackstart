"""Pass 3 live JLC price + stock refresh for every part added or re-counted in Pass 3 (read-only JLC parts search).
Writes fetch/price_<LCSC>.json and updates bom/lcsc_prices.csv (board main). Run from docs/split_evidence/modular_pass3."""
import json,subprocess,csv,io,time,os,collections
UA="Mozilla/5.0 (genctl-bom-final read-only lookup)"
ROOT='../../..'
CODES=['C113804','C22880','C22920','C14860','C353035','C81598','C2104','C22935','C28323','C28233','C1621','C23179','C22859','C23056','C20345924','C548409','C20917','C53658','C1517405']
qty=collections.Counter()
for r in csv.DictReader(open(f'{ROOT}/bom/genctl_main_bom.csv')):
    if r.get('LCSC') and r['Qty'].isdigit(): qty[r['LCSC']]+=int(r['Qty'])
def get(code):
    j=subprocess.run(['curl','-s','-m','25','-A',UA,'-H','Content-Type: application/json','-H','Origin: https://jlcpcb.com','-H','Referer: https://jlcpcb.com/parts',
        '-d',json.dumps({"keyword":code,"currentPage":1,"pageSize":5}),'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'],capture_output=True,text=True).stdout
    open(f'fetch/price_{code}.json','w').write(j)
    L=json.loads(j)['data']['componentPageInfo']['list'] or []
    return [x for x in L if x['componentCode']==code][0]
def tier(pr,n):
    best=None
    for p in sorted(pr,key=lambda p:p['startNumber']):
        if n>=p['startNumber']: best=p['productPrice']
    return best if best is not None else sorted(pr,key=lambda p:p['startNumber'])[0]['productPrice']
rows=list(csv.DictReader(open(f'{ROOT}/bom/lcsc_prices.csv'))); fields=list(rows[0].keys())
out=[]
for c in CODES:
    x=get(c); pr=x.get('componentPrices') or []; n=max(qty[c],1)
    rec=dict(board='main',key=c,lcsc_note=x.get('componentModelEn',''),**{'class':x.get('componentLibraryType','').replace('base','Basic').replace('expand','Extended')},
             stock=f"JLC {x.get('stockCount')}",unit_qty1=str(tier(pr,n)),unit_qty10=str(tier(pr,10*n)),source='JLC parts API live (Pass 3)',checked='2026-11-23 HST')
    out.append(rec); print(c,x.get('componentModelEn'),'qty/board',qty[c],'stock',x.get('stockCount'),x.get('componentLibraryType'),'unit',rec['unit_qty1'],rec['unit_qty10'])
    time.sleep(0.8)
keep=[r for r in rows if not (r['board']=='main' and r['key'] in CODES)]
with open(f'{ROOT}/bom/lcsc_prices.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL); w.writeheader()
    for r in sorted(keep+out,key=lambda r:(r['board'],r['key'])): w.writerow(r)
