import os,sys;os.environ['HVSHEET']='1';os.environ['NETS']=sys.argv[2]
sys.argv=['route_m7.py',sys.argv[1],'/tmp/x.kicad_pcb','1']
s=open('route_m7.py').read();s=s[:s.index('t0=time.time()')]
exec(s)
import scipy.ndimage as nd
hp,name,c,rep=jobs[0]
win=H.window(rep,25);y0,y1,x0,x1=win
w=H.width_of(c) if hasattr(H,'width_of') else 0.5
free,vfree,_=H.free_map(c,0.5,win)
src=H.pad_mask(c,win,[rep[0]])
# 3D reach: layers joined where vfree
st=np.zeros((3,3,3),bool);st[1]=nd.generate_binary_structure(2,1)
lab,_=nd.label(free|src,structure=st)
# merge layers through vias iteratively
R=np.isin(lab,np.unique(lab[src]))
for it in range(6):
  v=R.any(0)&vfree
  R=np.isin(lab,np.unique(lab[(free&v[None])|R]))
P=H.R;X0,Y0=H.X0,H.Y0
ys,xs=np.nonzero(R.any(0))
print('reach rows',y0,y1,'cols',x0,x1,'cells',R.sum(),'bbox mm x',X0+(x0+xs.min())*P,X0+(x0+xs.max())*P,'y',Y0+(y0+ys.min())*P,Y0+(y0+ys.max())*P)
for p in rep[1:]:
  t=H.pad_mask(c,win,[p]);print(p.GetParentFootprint().GetReference(),'reachable',bool((R&nd.binary_dilation(t,iterations=1)).any()))
from PIL import Image
img=np.zeros(R.shape[1:]+(3,),np.uint8)
img[...,0]=free[0]*80+R[0]*170; img[...,1]=free[1]*80+R[1]*170; img[...,2]=free[2]*80+R[2]*170
for p in rep:
  m=H.pad_mask(c,win,[p]).any(0); img[m]=255
Image.fromarray(img[:int(60/P)+1-0, :int(60/P)]).save('/tmp/reach.png')
