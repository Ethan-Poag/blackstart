import json,subprocess,sys,time,re
UA="Mozilla/5.0 (genctl read-only lookup)"
def q(kw,page,n=100):
    j=subprocess.run(['curl','-s','-m','30','-A',UA,'-H','Content-Type: application/json','-H','Origin: https://jlcpcb.com','-H','Referer: https://jlcpcb.com/parts','-d',json.dumps({"keyword":kw,"currentPage":page,"pageSize":n}),'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'],capture_output=True,text=True).stdout
    try: return json.loads(j)['data']['componentPageInfo']['list'] or []
    except: return []
kw=sys.argv[1]; pat=re.compile(sys.argv[2]); seen=set()
for p in range(1,int(sys.argv[3]) if len(sys.argv)>3 else 6):
    L=q(kw,p)
    if not L: break
    for x in L:
        d=(x.get('describe') or '')+' '+(x.get('componentSpecificationEn') or '')
        if pat.search(d) and x['componentCode'] not in seen:
            seen.add(x['componentCode']); pr=x.get('componentPrices') or []
            print(x['componentCode'],x.get('componentModelEn'),'|',x.get('componentBrandEn'),'| stock',x.get('stockCount'),'|',x.get('componentLibraryType'),'| $',pr[0]['productPrice'] if pr else None,'|',d[:200])
    time.sleep(0.6)
