import subprocess,re,json,sys
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def inv(opn):
    j=subprocess.run(['curl','-s','-m','20','-A',UA,f'https://www.ti.com/storeservices/cart/opninventory?opn={opn}'],capture_output=True,text=True).stdout
    try: return json.loads(j)['inventory']
    except: return None
def price(prod,opn):
    t=subprocess.run(['curl','-s','-m','25','-L','-A',UA,f'https://www.ti.com/product/{prod}/part-details/{opn}'],capture_output=True,text=True).stdout
    m=re.search(r'"price":\s*"([0-9.]+)"',t); return m.group(1) if m else None
for a in sys.argv[1:]:
    prod,opn=a.split(':'); print(opn,'TI stock',inv(opn),'TI price(JSON-LD)',price(prod,opn))
