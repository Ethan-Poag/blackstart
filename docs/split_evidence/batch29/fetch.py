import json,subprocess,time,os,sys
UA="Mozilla/5.0 (genctl-bom-final read-only lookup)"
codes=sys.argv[1:] or sorted({o['lcsc'] for o in json.load(open('x'))['groups']})
def curl(a): return subprocess.run(['curl','-s','-m','25','-A',UA]+a,capture_output=True,text=True).stdout
for c in codes:
    if os.path.exists(f'fetch/jlc_{c}.json') and os.path.getsize(f'fetch/jlc_{c}.json')>100 and os.path.exists(f'fetch/lcsc_{c}.json') and os.path.getsize(f'fetch/lcsc_{c}.json')>100: continue
    j=curl(['-H','Content-Type: application/json','-H','Origin: https://jlcpcb.com','-H','Referer: https://jlcpcb.com/parts','-d',json.dumps({"keyword":c,"currentPage":1,"pageSize":5}),'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'])
    open(f'fetch/jlc_{c}.json','w').write(j); time.sleep(0.7)
    l=curl([f'https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={c}'])
    open(f'fetch/lcsc_{c}.json','w').write(l); time.sleep(0.7)
    print(c,time.strftime('%H:%M:%S'),len(j),len(l),flush=True)
print('DONE',flush=True)
