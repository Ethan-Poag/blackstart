import json,subprocess,sys,time
UA="Mozilla/5.0 (genctl-bom-final read-only lookup)"
def s(kw,n=10):
    j=subprocess.run(['curl','-s','-m','25','-A',UA,'-H','Content-Type: application/json','-H','Origin: https://jlcpcb.com','-H','Referer: https://jlcpcb.com/parts','-d',json.dumps({"keyword":kw,"currentPage":1,"pageSize":n}),'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'],capture_output=True,text=True).stdout
    open(f'fetch/search_{kw.replace("/","_").replace(" ","_")}.json','w').write(j)
    try: L=json.loads(j)['data']['componentPageInfo']['list'] or []
    except Exception as e: print(kw,'ERR',j[:200]); return
    print('==',kw)
    for x in L:
        pr=x.get('componentPrices') or []
        print('  ',x['componentCode'],x.get('componentModelEn'),'|',x.get('componentBrandEn'),'| stock',x.get('stockCount'),'|',x.get('componentLibraryType'),'| $',pr[0]['productPrice'] if pr else None,'|',(x.get('componentSpecificationEn') or ''),'|',(x.get('describe') or '')[:90])
for kw in sys.argv[1:]: s(kw); time.sleep(0.8)
