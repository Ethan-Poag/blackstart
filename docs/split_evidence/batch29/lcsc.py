import json,subprocess,sys
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(code):
    j=subprocess.run(['curl','-s','-m','25','-A',UA,f'https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={code}'],capture_output=True,text=True).stdout
    return json.loads(j)['result']
if __name__=='__main__':
    out={}
    for c in sys.argv[1:]:
        try: r=get(c)
        except Exception as e: print(c,'ERR',e); continue
        pr=[(p.get('ladder'),p.get('usdPrice') or p.get('productPrice')) for p in (r.get('productPriceList') or [])][:4]
        imgs=r.get('productImages') or []
        print(c, r.get('productModel'),'|',r.get('brandNameEn'),'| LCSC stock',r.get('stockNumber'),'| price',pr,'| pkg',r.get('encapStandard'))
        print('   pdf',r.get('pdfUrl')); print('   imgs',imgs[:3])
        out[c]=r
    json.dump(out,open('/workspace/review/fix29/lcsc_'+'_'.join(sys.argv[1:3])+'.json','w'))
