import sys,os
os.environ['HVSHEET']='1';os.environ['NETS']='GEN_L2'
sys.argv=['route_m7.py','a6b.kicad_pcb','/tmp/x.kicad_pcb','1']
src=open('route_m7.py').read();src=src[:src.index('PLANE=(')]
exec(src)
c=[n.GetNetCode() for n in b.GetNetsByNetcode().values() if n.GetNetname().endswith('/GEN_L2')][0]
x0,x1,y0,y1=int(H.gx(0)),int(H.gx(40)),int(H.gy(30)),int(H.gy(46))
free,vfree,_=H.free_map(c,0.5,(y0,y1,x0,x1))
for l in range(3):
  print('layer',l)
  for yy in range(0,y1-y0,5):
    print(''.join('#' if not free[l,yy,xx] else '.' for xx in range(0,x1-x0,5)))
print('via');
for yy in range(0,y1-y0,5): print(''.join('#' if not vfree[yy,xx] else '.' for xx in range(0,x1-x0,5)))
