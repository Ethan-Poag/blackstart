import json,subprocess,sys,time
UA="Mozilla/5.0 (genctl-bom read-only lookup)"
def curl(a): return subprocess.run(['curl','-s','-m','25','-A',UA]+a,capture_output=True,text=True).stdout
def jlc(kw,n=25):
    j=curl(['-H','Content-Type: application/json','-H','Origin: https://jlcpcb.com','-H','Referer: https://jlcpcb.com/parts','-d',json.dumps({"keyword":kw,"currentPage":1,"pageSize":n}),'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'])
    try: d=json.loads(j)
    except Exception: print('ERR',j[:200]); return []
    return (d.get('data') or {}).get('componentPageInfo',{}).get('list') or []
if __name__=='__main__':
    for kw in sys.argv[1:]:
        for c in jlc(kw):
            print(kw,'|',c.get('componentCode'),c.get('componentModelEn'),'|',c.get('componentBrandEn'),'|',c.get('componentSpecificationEn'),'| JLC',c.get('stockCount'),'|',c.get('componentLibraryType'),'|',(c.get('componentPrices') or [{}])[0].get('productPrice'))
        time.sleep(0.7)
