#!/usr/bin/env python3
"""Pass 5 pre-check: VBAT_P / BAT_IN inductive kick when a slot latches off a dead short.
Two-node model with the REAL power.kicad_sch parts (netlist audit 2026-11-23):
  battery Vb - Rb - Lb -> BAT_IN [C297 220n X7R, D1 TVS, U1 A pin, OV divider R1/R2/R3 = 210k/49.9k/8.66k]
  -> Q1 (ideal diode) + Q2 (U1 HGATE) + R555 2 mOhm, loop Lf -> VBAT_P [C5-C8 4x10u X7S 100 V, C38 2.2u, C39/C233,
     C3/C4 2x EEETG1J101UP 100u 63 V (800 mOhm @100 kHz), D2 TVS] -> bank Rd1 -> VBAT_SLOTS (Cs) -> slot Ls/Rd2 dead short.
Slot latch at t_SC(1.0 nF C0G, max) + t_prop = 25.2 us, slot FET turn-off ramp t_off (G1PD 2 A: 0.5 us).
U1 modes: 'on' = Q2 forced on (case a); 'ov' = real LM74800 OV: BAT_IN/31.01 > V_OVR (1.195/1.267 V) for t_deg
(3.98 typ / 5.4 max us), then HGATE 168 mA sink -> Q2 off in ~0.2 us; Q2 then blocks until V(BR)DSS (100 V min,
avalanche modelled 110 V + 20 mOhm); Q1 blocks reverse. Optional C_OV on the OV pin (RC with the divider Thevenin R).
TVS: V = VBR_max + Rd*I, Rd = (VC - VBR_max)/Ipp (datasheet/JLC values), linear above Ipp.
No load current (worst case). numpy-vectorised over the reviewer grid Rb 15/35 mOhm x Lb 0.5/2 uH x Rd2 12/25 mOhm x
cap corner (nominal / cold-aged).
"""
import itertools, numpy as np, sys
F=lambda c: c*9/5+32
T_LATCH=25.2e-6
OV_RATIO=(210e3+49.9e3+8.66e3)/8.66e3; R_OV_TH=8.66e3*(210e3+49.9e3)/(210e3+49.9e3+8.66e3)
TVS={ # name: (VBR_min, VBR_max, VC, Ipp)   sources: JLC listing + Littelfuse/Vishay datasheets in evidence
 'SMBJ40CA (D2 as built, 600 W)':(44.4,49.1,64.5,9.3),
 'SMDJ40CA (D1 as built, 3 kW)':(44.4,49.1,64.5,46.5),
 '5.0SMDJ33A':(36.7,40.6,53.3,93.9),
 '5.0SMDJ36CA':(40.0,44.2,58.1,86.1),
 '5.0SMDJ40CA':(44.4,49.1,64.5,77.6),
 'SM8S33A (6.6 kW)':(36.7,40.6,53.3,124.0),
 'SM8S36A (6.6 kW)':(40.0,44.2,58.1,114.0),
 'none':None,
}
def tvs_i(v,name,n=1):
    p=TVS[name]
    if p is None: return 0.0*v
    vbr=p[1]; rd=(p[2]-p[1])/p[3]
    return n*np.maximum(v-vbr,0.0)/rd

ZTH=[(1e-6,0.0085),(3e-6,0.016),(1e-5,0.040),(3e-5,0.085),(1e-4,0.195),(3e-4,0.36),(1e-3,0.545),(1e-2,1.16),(1e-1,1.49)]  # BSC070N10NS5 Diagram 4 (as pass4_calc)
import math
def zth(t):
    if t<=0: return 0.0
    if t<=ZTH[0][0]: return ZTH[0][1]*(t/ZTH[0][0])**0.64
    for (t1,z1),(t2,z2) in zip(ZTH,ZTH[1:]):
        if t1<=t<=t2: return math.exp(math.log(z1)+(math.log(z2)-math.log(z1))*(math.log(t)-math.log(t1))/(math.log(t2)-math.log(t1)))
    return ZTH[-1][1]
def tj_rise(P,dt):
    Z=np.array([zth((k+0.5)*dt) for k in range(len(P)+1)]); dP=np.diff(np.concatenate([[0.0],P]))
    return max(float(np.dot(dP[:m+1],Z[m::-1][:m+1])) for m in range(len(P)))
RDS125=7e-3*(1+0.0064*100); SHARE=0.55
GRID=list(itertools.product([0.015,0.035],[0.5e-6,2e-6],[0.012,0.025],[0,1]))
def run(Vb,d1='SMDJ40CA (D1 as built, 3 kW)',d2='SMBJ40CA (D2 as built, 600 W)',d2n=1,bulk=(('elec',2),),mode='ov',
        vovr=1.195,tdeg=3.98e-6,c_ov=0.0,t_off=0.5e-6,Rfe=0.013,Lf=10e-9,Rd1=0.010,Cs=0.9e-6,Ls=50e-9,T=140e-6,dt=2e-9,extra_mlcc=0.0,r_u65=1.0,i_u65=5e-3,rcd=False,rcd_vf=0.6,rcd_r=0.004,rcd_bleed=10.0,tj_off=True):
    G=np.array(GRID); Rb=G[:,0]; Lb=G[:,1]; Rd2=G[:,2]; cold=G[:,3]>0
    n=len(G)
    # VBAT_P ceramics: 4x10u X7S 100 V at ~32-45 V bias ~0.65 (nominal) / 0.55 (cold-aged); C38 2.2u x0.6; 2x100n
    Cc=np.where(cold,4*10e-6*0.55+2.2e-6*0.5,4*10e-6*0.65+2.2e-6*0.6)+0.2e-6+extra_mlcc*np.where(cold,0.55,0.65)
    CB=0.22e-6*0.8+0.05e-6              # C297 220n X7R 100 V at bias + D1/Q1 capacitance
    caps=[]                              # bulk branches: (C, ESR array)
    for kind,k in bulk:
        if kind=='elec':   C,E,ec=100e-6,0.8,4.0    # EEETG1J101UP: 800 mOhm @100 kHz 68 F; cold -40 F x4
        elif kind=='zu150':C,E,ec=150e-6,0.010,2.0  # EEH-ZU1J151V hybrid 63 V 10 mOhm
        elif kind=='zc56': C,E,ec=56e-6,0.030,2.0   # EEHZC1J560P hybrid 63 V 30 mOhm
        elif kind=='hx82': C,E,ec=82e-6,0.030,2.0   # HHXC630ARA820MJA0G hybrid 63 V 30 mOhm
        for _ in range(k): caps.append([np.full(n,Vb), C*np.where(cold,0.8,1.0), E*np.where(cold,ec,1.0)])
    iL=np.zeros(n); iF=np.zeros(n); vB=np.full(n,Vb); vP=np.full(n,Vb); vS=np.full(n,Vb); i2=np.zeros(n)
    vov=np.full(n,Vb/OV_RATIO); tau_ov=R_OV_TH*c_ov
    trip=np.full(n,np.inf); qoff=np.full(n,np.inf); ilatch=None
    pkB=np.full(n,Vb); pkP=np.full(n,Vb); EQ2=np.zeros(n); ED1=np.zeros(n); ED2=np.zeros(n); Eslot=np.zeros(n)
    tripped=np.zeros(n,bool); iLl=np.zeros(n)
    vU=np.full(n,Vb-0.5); pkU=vU.copy(); Ps=[]; Pk=[]; ipk2=np.zeros(n); ipk1=np.zeros(n); samp=int(round(0.1e-6/dt)); step=0
    t=0.0
    while t<T:
        # Q2 state
        if mode=='on': vq2=0.0*vB; frac=0.0*vB
        else:
            frac=np.clip((t-qoff)/0.2e-6,0,1); vq2=110.0*frac
        # forward path (Lf, Rfe, Q2 blocking voltage); Q1 ideal diode blocks reverse
        if mode=='on': diF=(vB-vP-iF*Rfe)/Lf
        else:
            on=frac<=0
            diF=np.where(on,(vB-vP-iF*Rfe)/Lf,(vB-vP-np.maximum(vq2,0)-iF*(Rfe+0.02))/Lf)
        iF=np.maximum(iF+diF*dt,0.0)
        EQ2+=np.where(frac>0,vq2*iF,0)*dt
        iD1=tvs_i(vB,d1); iD2=tvs_i(vP,d2,d2n)
        ED1+=iD1*vB*dt; ED2+=iD2*vP*dt
        iL+=(Vb-iL*Rb-vB)/Lb*dt
        vB+=(iL-iF-iD1)/CB*dt
        ib=0.0
        if rcd:   # diode-isolated bulk: charges only through the steering diode(s), bleeds back through rcd_bleed
            vE=caps[0][0]; Ctot=sum(c[1] for c in caps); Etot=1/sum(1/c[2] for c in caps)
            i=np.maximum(vP-vE-rcd_vf,0)/(Etot+rcd_r)-(vE-vP)/rcd_bleed
            for c in caps: c[0]=vE+i/Ctot*dt
            ib=i
        else:
          for c in caps:
            i=(vP-c[0])/c[2]; c[0]=c[0]+i/c[1]*dt; ib=ib+i
        i1=(vP-vS)/Rd1
        vP+=(iF-ib-i1-iD2)/Cc*dt
        if t<T_LATCH: i2+=(vS-i2*Rd2)/Ls*dt; vfet=0
        else:
            if ilatch is None: ilatch=i2.copy(); iLl=iL.copy()
            on2=max(0.0,1.0-(t-T_LATCH)/t_off); inew=ilatch*on2
            vfet=vS-inew*Rd2-Ls*(inew-i2)/dt; Eslot+=np.maximum(vfet,0)*inew*dt; i2=inew
        vS+=(i1-i2)/Cs*dt
        ipk2=np.maximum(ipk2,i2); ipk1=np.maximum(ipk1,i1)
        if step%samp==0 and t<=T_LATCH+t_off+0.2e-6:
            Ps.append((SHARE*i2)**2*RDS125+(SHARE*np.maximum(vfet,0)*i2 if (t>=T_LATCH and tj_off) else 0)); Pk.append((SHARE*i1)**2*RDS125)
        step+=1
        # OV comparator with optional RC
        if tau_ov>0: vov+=(vB/OV_RATIO-vov)/tau_ov*dt
        else: vov=vB/OV_RATIO
        if mode=='ov':
            newt=(vov>vovr)&~np.isfinite(trip); trip[newt]=t
            below=vov<1.091
            trip[below&np.isfinite(trip)&(t-trip<tdeg)]=np.inf   # deglitch reset if it falls back
            fire=np.isfinite(trip)&(t-trip>=tdeg)&~np.isfinite(qoff); qoff[fire]=t; tripped|=fire
        vU+=(np.maximum(vP-0.45-vU,0)/r_u65-i_u65)/10e-6*0.75*dt; pkU=np.maximum(pkU,vU)   # D120 SS110 + C225 10u X7S (bias) feeding U65
        pkB=np.maximum(pkB,vB); pkP=np.maximum(pkP,vP)
        t+=dt
    Ps=np.array(Ps); Pk=np.array(Pk)
    dTj=np.array([tj_rise(Ps[:,j],0.1e-6) for j in range(n)]); dTjb=np.array([tj_rise(Pk[:,j],0.1e-6) for j in range(n)])
    return dict(dTj=dTj,dTjb=dTjb,ipk2=ipk2,ipk1=ipk1,pkU=pkU,pkB=pkB,pkP=pkP,tripped=tripped,EQ2=EQ2,ED1=ED1,ED2=ED2,Eslot=Eslot,iLl=iLl,ilatch=ilatch)

def hotplug(Vb,bulk=(('elec',2),),rcd=False,c_dvdt=0.0,cgd=28e-12,K=30.0,Vt=2.86,ihg=75e-6,Rb=0.015,Lb=0.5e-6,Rfe=0.008,T=3e-3,dt=2e-9,Tc=65.0):
    """Q2 turn-on into VBAT_P with VBAT_DD already at Vb (U1 charge pump up). HGATE sources ihg (75 uA max) into Cgs (2.1 nF), Cgd and
    an optional C_dVdT HGATE->GND (TI inrush method). Q2 saturation I = K (Vgs-Vt)^2 (BSC070 fast corner, as pass4_calc).
    Returns peak inrush, Q2 energy, Q2 dTj (ZthJC Diagram 4, Tc 149 F) and F1 I2t."""
    Cc=4*10e-6*0.65+2.2e-6*0.6+0.2e-6; caps=[]
    for kind,k in bulk:
        C,E={'elec':(100e-6,0.8),'zu150':(150e-6,0.010),'zc56':(56e-6,0.030),'hx82':(82e-6,0.030)}[kind]
        for _ in range(k): caps.append([0.0,C,E])
    vg=0.0; vp=0.0; vdd=Vb; iL=0.0; E=0.0; I2t=0.0; ipk=0.0; P=[]; t=0.0; acc=0.0; nacc=0; samp=int(round(1e-6/dt)); step=0
    while t<T:
        vgs=vg-vp; iD=K*max(vgs-Vt,0)**2
        vds=vdd-vp
        # Q2 fully on: resistive
        iD=min(iD,max(vds,0)/Rfe)
        if rcd:
            vE=caps[0][0]; Ct=sum(c[1] for c in caps); Et=1/sum(1/c[2] for c in caps)
            ib=max(vp-vE-0.6,0)/(Et+0.004)-(vE-vp)/10.0
            for c in caps: c[0]=vE+ib/Ct*dt
        else:
            ib=0.0
            for c in caps:
                i=(vp-c[0])/c[2]; c[0]+=i/c[1]*dt; ib+=i
        dvp=(iD-ib)/Cc*dt
        # gate: ihg = Cgs d(vg-vp) + (Cgd+Cdvdt) dvg  -> solve for dvg
        dvg=(ihg*dt+2.1e-9*dvp)/(2.1e-9+cgd+c_dvdt)
        vp+=dvp; vg=min(vg+dvg,vp+11.1)
        iL+=(Vb-iL*Rb-vdd)/Lb*dt; vdd+=(iL-iD)/2e-6*dt   # VBAT_DD/BAT_IN local caps ~2 uF incl. C297, C1
        E+=iD*max(vds,0)*dt; I2t+=iL*iL*dt; ipk=max(ipk,iL)
        acc+=iD*max(vds,0); nacc+=1
        if step%samp==0: P.append(acc/max(nacc,1)); acc=0.0; nacc=0
        step+=1; t+=dt
        if vp>Vb-0.3 and t>50e-6 and iD<0.5: break
    P=np.array(P); 
    return dict(ipk=ipk,E=E,I2t=I2t,dTj=tj_rise(P,1e-6) if len(P) else 0.0,t=t)

SCEN=[
 ('A  as built: D1 SMDJ40CA, D2 SMBJ40CA, C3/C4 2x EEETG1J101UP',dict()),
 ('B  D1+D2 -> SM8S36A (6.6 kW DO-218AB)',dict(d1='SM8S36A (6.6 kW)',d2='SM8S36A (6.6 kW)')),
 ('C  B + C_OV 100 nF on U1 OV pin',dict(d1='SM8S36A (6.6 kW)',d2='SM8S36A (6.6 kW)',c_ov=100e-9)),
 ('D  D2 SM8S36A + C3/C4 -> 4x EEH-ZU1J151V direct on VBAT_P',dict(d2='SM8S36A (6.6 kW)',bulk=(('zu150',4),))),
 ('E  D + C_OV 100 nF',dict(d2='SM8S36A (6.6 kW)',bulk=(('zu150',4),),c_ov=100e-9)),
 ('F  D2 SM8S36A + 4x ZU1J151V diode-steered (RCD) + C_OV 100 nF',dict(d2='SM8S36A (6.6 kW)',bulk=(('zu150',4),),rcd=True,c_ov=100e-9)),
 ('G  F with C_OV 47 nF',dict(d2='SM8S36A (6.6 kW)',bulk=(('zu150',4),),rcd=True,c_ov=47e-9)),
 ('H  F with 2x ZU1J151V',dict(d2='SM8S36A (6.6 kW)',bulk=(('zu150',2),),rcd=True,c_ov=100e-9)),
]
if __name__=='__main__':
    import multiprocessing as mp
    def one(a):
        i,V=a; lab,kw=SCEN[i]; r=run(V,**kw)
        return i,V,r['pkP'].max(),r['pkB'].max(),r['pkU'].max(),int(r['tripped'].sum()),r['ipk2'].max(),r['dTj'].max(),r['iLl'].max(),r['ED2'].max()*1e3,r['ED1'].max()*1e3
    jobs=[(i,V) for i in range(len(SCEN)) for V in (12.6,24.0,28.8,32.0)]
    with mp.Pool(min(8,mp.cpu_count())) as p: res=p.map(one,jobs)
    print(__doc__)
    print('Limits: VBAT_P target <= 52 V (LM5176 U2 VIN abs max 60 V, ROC 55 V; TPS1HTC30 U68 VS 64 V; TPS26621 U89 IN 62 V; LMR36506 U5 70 V)')
    print('        BAT_IN target <= 62 V (LM74800 U1 A abs max 70 V; C297 100 V); U65 TPS7B6950 IN abs max 45 V (via D120 SS110 + C225 10 uF)')
    print('Worst of 16 corners (Rb 15/35 mOhm x Lb 0.5/2 uH x Rd2 12/25 mOhm x caps nominal/cold-aged); slot latch 25.2 us; Tj rise incl. 0.5 us turn-off loss, Tc 149 F (65 C) start\n')
    print('%-64s %5s %7s %7s %6s %7s %7s %8s %8s %6s %6s'%('scenario','Vbat','VBAT_P','BAT_IN','U65','OVtrip','slotIpk','slotdTj','iL@latch','E_D2','E_D1'))
    for i,V,P,B,U,tr,ip,dt_,il,e2,e1 in res:
        print('%-64s %5.1f %6.1fV %6.1fV %5.1fV %4d/16 %6.0fA %6.0fK %7.0fA %4.0fmJ %4.0fmJ'%(SCEN[i][0],V,P,B,U,tr,ip,dt_,il,e2,e1))
    print('\nHot-plug at 32 V, Q2 turn-on with HGATE 75 uA (no C_dVdT in the as-built schematic), Lb 0.5 uH, Rb 15 mOhm, Tc 149 F (65 C):')
    for lab,kw in (('as built (2x EEETG1J101UP)',{}),('4x ZU1J151V direct',dict(bulk=(('zu150',4),))),('4x ZU1J151V diode-steered',dict(bulk=(('zu150',4),),rcd=True)),('4x ZU1J151V diode-steered + C_dVdT 22 nF HGATE-GND',dict(bulk=(('zu150',4),),rcd=True,c_dvdt=22e-9))):
        for cgd in (28e-12,200e-12):
            slow='dVdT' in lab
            r=hotplug(32.0,cgd=cgd,dt=2e-8 if slow else 5e-9,T=40e-3 if slow else 3e-3,**kw)
            print('  %-50s Cgd %3.0f pF: inrush pk %4.0f A, Q2 E %4.0f mJ, Q2 dTj %4.0f K -> Tj %4.0f F (%3.0f C), F1 I2t %.2f A2s, ramp %.1f ms'%(lab,cgd*1e12,r['ipk'],r['E']*1e3,r['dTj'],F(65+r['dTj']),65+r['dTj'],r['I2t'],r['t']*1e3))
