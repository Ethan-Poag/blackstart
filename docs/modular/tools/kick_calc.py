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

def hotplug(Vb,bulk=(('elec',2),),rcd=False,c_dvdt=0.0,cgd=28e-12,K=30.0,Vt=2.86,ihg=75e-6,Rb=0.015,Lb=0.5e-6,Rfe=0.008,T=3e-3,dt=2e-9,Tc=65.0,
            p_load=0.0,v_on=4.96,v_off=4.6,t_ss=7.5e-3,eta=0.88,c_uvlo=0.0,load_shape='lin'):
    """Q2 turn-on into VBAT_P with VBAT_DD already at Vb (U1 charge pump up). HGATE sources ihg (75 uA max) into Cgs (2.1 nF), Cgd and
    an optional C_dVdT HGATE->GND (TI inrush method). Q2 saturation I = K (Vgs-Vt)^2 (BSC070 fast corner, as pass4_calc).
    Returns peak inrush, Q2 energy, Q2 dTj (ZthJC Diagram 4, Tc 149 F) and F1 I2t.
    Pass 5: optional converter load p_load (W, input side = p/eta): starts when VBAT_P passes v_on (LM5176 UVLO 4.96 V, R4/R5
    100k/33k), ramps linearly over t_ss (C10 47 nF soft start ~7.5 ms), drops out below v_off. c_uvlo: capacitor on the LM5176
    EN/UVLO node (Thevenin 24.8k): the converter starts when that node passes 1.23 V. load_shape 'lin' (P ~ t) or 'res' (P ~ t^2,
    resistive loads on a ramping +12 V). Returns a 10 us trace (vds, iD) for the SOA check."""
    Cc=4*10e-6*0.65+2.2e-6*0.6+0.2e-6; caps=[]
    for kind,k in bulk:
        C,E={'elec':(100e-6,0.8),'zu150':(150e-6,0.010),'zc56':(56e-6,0.030),'hx82':(82e-6,0.030)}[kind]
        for _ in range(k): caps.append([0.0,C,E])
    vg=0.0; vp=0.0; vdd=Vb; iL=0.0; E=0.0; I2t=0.0; ipk=0.0; P=[]; t=0.0; acc=0.0; nacc=0; samp=int(round(1e-6/dt)); step=0; t_on=None; ild=0.0; iDpk=0.0
    t_on_pred=None; vn=0.0; trv=[]; tri=[]; av=0.0; ai=0.0; na=0; s10=max(1,int(round(1e-5/dt)))
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
        if p_load>0:
            if c_uvlo>0: vn+=((vp*33/133-vn)/24.8e3)/c_uvlo*dt
            else: vn=vp*33/133
            if t_on is None and vn>=v_on*33/133 and vp>=v_on: t_on=t
            if t_on is not None and vp<v_off: t_on=None
            x=min(1.0,(t-t_on)/t_ss) if t_on is not None else 0.0
            ild=p_load*(x if load_shape=='lin' else x*x)/eta/max(vp,1.0)
        dvp=(iD-ib-ild)/Cc*dt
        # gate: ihg = Cgs d(vg-vp) + (Cgd+Cdvdt) dvg  -> solve for dvg
        dvg=(ihg*dt+2.1e-9*dvp)/(2.1e-9+cgd+c_dvdt)
        vp+=dvp; vg=min(vg+dvg,vp+11.1)
        iL+=(Vb-iL*Rb-vdd)/Lb*dt; vdd+=(iL-iD)/2e-6*dt   # VBAT_DD/BAT_IN local caps ~2 uF incl. C297, C1
        E+=iD*max(vds,0)*dt; I2t+=iL*iL*dt; ipk=max(ipk,iL); iDpk=max(iDpk,iD)
        acc+=iD*max(vds,0); nacc+=1
        av+=max(vds,0); ai+=iD; na+=1
        if na>=s10: trv.append(av/na); tri.append(ai/na); av=ai=0.0; na=0
        if step%samp==0: P.append(acc/max(nacc,1)); acc=0.0; nacc=0
        step+=1; t+=dt
        if vp>Vb-0.3 and t>50e-6 and iD<ild+0.5 and (p_load==0 or (t_on is not None and t>t_on+t_ss)): break
        if p_load>0 and c_uvlo>0 and t_on is None and vp>Vb-0.3 and t>50e-6 and iD<0.5:
            # VBAT_P is up and Q2 fully on before U2 starts: the converter load then sees Q2 at Vds ~ 0 (no linear-mode stress).
            vth=v_on*33/133; vinf=vp*33/133
            t_on_pred=t+(24.8e3*c_uvlo*math.log((vinf-vn)/(vinf-vth)) if vinf>vth else float('inf')); break
    P=np.array(P); 
    return dict(ipk=ipk,iDpk=iDpk,E=E,I2t=I2t,dTj=tj_rise(P,1e-6) if len(P) else 0.0,t=t,t_on=t_on,t_on_pred=t_on_pred,vds=np.array(trv),iD=np.array(tri))

# BSC070N10NS5 Diagram 3 (SOA, Tc 77 F / 25 C, single pulse), digitised from the 400 dpi render (docs/split_evidence/modular_pass5/
# bsc070_soa.png): 1 ms, 10 ms and DC lines follow I = A / V^2 (Spirito-limited linear mode); 100 us is piecewise.
SOA_100US=[(10,74.8),(20,31.5),(40,7.77),(90,1.54)]
SOA_A={1e-3:1160.0,1e-2:359.0,1.0:167.0}
def soa_i(V,tau):
    V=max(V,1.0)
    def l100(V):
        pts=SOA_100US
        if V<=pts[0][0]: return pts[0][1]*(pts[0][0]/V)
        for (v1,i1),(v2,i2) in zip(pts,pts[1:]):
            if v1<=V<=v2: return math.exp(math.log(i1)+(math.log(i2)-math.log(i1))*(math.log(V)-math.log(v1))/(math.log(v2)-math.log(v1)))
        return pts[-1][1]*(pts[-1][0]/V)**2
    lines=[(1e-4,l100(V))]+[(t,A/V/V) for t,A in sorted(SOA_A.items())]
    if tau<=lines[0][0]: return lines[0][1]
    for (t1,i1),(t2,i2) in zip(lines,lines[1:]):
        if t1<=tau<=t2: return math.exp(math.log(i1)+(math.log(i2)-math.log(i1))*(math.log(tau)-math.log(t1))/(math.log(t2)-math.log(t1)))
    return lines[-1][1]
def soa_check(vds,iD,Tc=65.0,dt=1e-5):
    """Worst sliding-window ratio I_avg / (SOA(V_eff, tau) x (150-Tc)/125) for tau = 0.1/1/10 ms and the whole event;
    V_eff = P_avg / I_avg. Returns (ratio, tau, V_eff, I_avg)."""
    der=(150.0-Tc)/125.0; best=(0.0,0,0,0); n=len(vds)
    if n==0: return best
    P=np.concatenate([[0.0],np.cumsum(vds*iD)]); I=np.concatenate([[0.0],np.cumsum(iD)])
    for tau in (1e-4,1e-3,1e-2,n*dt):
        w=max(1,min(n,int(round(tau/dt))))
        Ia=(I[w:]-I[:-w])/w if w<n else np.array([I[-1]/n]); Pa=(P[w:]-P[:-w])/w if w<n else np.array([P[-1]/n])
        for k in np.argsort(-Pa)[:200]:
            if Ia[k]<=1e-3: continue
            Ve=Pa[k]/Ia[k]; r=Ia[k]/(soa_i(Ve,w*dt)*der)
            if r>best[0]: best=(r,w*dt,Ve,Ia[k])
    return best


# ---------------- Pass 5: slots on TPS16630 eFuses (Ethan 2026-11-23 10:20 PM HST) ----------------
TVS['SMBJ40CA per slot (IN)']=(44.4,49.1,64.5,9.3)
def run_ef(Vb,I_scp=45.0,t_resp=1.0e-6,t_ramp=0.2e-6,t_hold=5e-6,I_ol=6.30,Ron=0.019,Lbank=60e-9,Rd1=0.010,
           Cs_slot=1e-6,n_slot=8,tvs_in=None,Ls=50e-9,v_sch=1.2,r_sch=0.020,T=120e-6,dt=1e-9,r_u65=48.0,i_u65=5e-3,
           d1='SMDJ40CA (D1 as built, 3 kW)',d2='SMBJ40CA (D2 as built, 600 W)',bulk=(('elec',2),),vovr=1.195,tdeg=3.98e-6,
           hgate_extra=1.0e-6,ipk_cap=None,ovp_min=1.176*(453e3+10e3*1.01)/(10e3*1.01)):
    """Dead short at a slot output (card side), slot switch = TPS16630 (SLVSET9G): integrated FET Ron (19 mOhm min / 53 max);
    fast-trip/hot-short comparator I(SCP) 45 A typ -> FET off after t_resp (1 us typ; 'few us' hold-off), then the current-limit loop
    re-enters at I(OL) (Pass 6 M2: 3.09k, 5.36-6.30 A incl. 1 % R; was 4.02k) until TSD -> latch (MODE open). Output-side loop Ls freewheels through the SS310B
    Schottky (OUT->GND, Vf ~1.2 V at high current). VBAT_SLOTS = per-slot C_IN (1 uF/100 V X7R, -40 % bias) + 100 nF at every slot
    (lumped; the faulted slot's caps sit right at its IN pin, the bus inductance Lbank (bank FETs, 5 mOhm shunt, backplane bus) sits
    between VBAT_P and VBAT_SLOTS). U1 OV with the real deglitch; the new 22 nF + 1k on HGATE adds hgate_extra to Q2 turn-off.
    U65 behind D120 + 47R + C225 10 uF. ipk_cap: optional eFuse saturation-current cap (A) for the realistic case."""
    G=np.array(GRID); Rb=G[:,0]; Lb=G[:,1]; Rd2=G[:,2]; cold=G[:,3]>0; n=len(G)
    Cc=np.where(cold,4*10e-6*0.55+2.2e-6*0.5,4*10e-6*0.65+2.2e-6*0.6)+0.2e-6
    CB=0.22e-6*0.8+0.05e-6
    Cs=n_slot*(Cs_slot*np.where(cold,0.5,0.6)+0.1e-6*0.63)+0.2e-6
    caps=[]
    for kind,k in bulk:
        C,E,ec={'elec':(100e-6,0.8,4.0)}[kind]
        for _ in range(k): caps.append([np.full(n,Vb),C*np.where(cold,0.8,1.0),E*np.where(cold,ec,1.0)])
    iL=np.zeros(n); iF=np.zeros(n); vB=np.full(n,Vb); vP=np.full(n,Vb); vS=np.full(n,Vb); iK=np.zeros(n); iO=np.zeros(n)
    vU=np.full(n,Vb-0.5); vov=np.full(n,Vb/OV_RATIO)
    state=np.zeros(n,int)   # 0 on, 1 detected, 2 ramp, 3 hold, 4 current limit
    tdet=np.full(n,np.inf); tramp=np.full(n,np.inf); i_at=np.zeros(n); trip=np.full(n,np.inf); qoff=np.full(n,np.inf)
    pk=dict(vP=np.full(n,Vb),vB=np.full(n,Vb),vS=np.full(n,Vb),vU=vU.copy(),ief=np.zeros(n),iK=np.zeros(n),iL=np.zeros(n),vout_neg=np.zeros(n))
    E_ef=np.zeros(n); E_sch=np.zeros(n); E_bank=np.zeros(n); I2t=np.zeros(n); tripped=np.zeros(n,bool); t_ovp=np.zeros(n); vS_lo=np.full(n,Vb)
    t=0.0
    while t<T:
        frac=np.clip((t-qoff)/0.2e-6,0,1); vq2=110.0*frac
        on=frac<=0
        diF=np.where(on,(vB-vP-iF*0.013)/10e-9,(vB-vP-vq2-iF*0.033)/10e-9)
        iF=np.maximum(iF+diF*dt,0.0)
        iD1=tvs_i(vB,d1); iD2=tvs_i(vP,d2)
        iL+=(Vb-iL*Rb-vB)/Lb*dt
        vB+=(iL-iF-iD1)/CB*dt
        ib=0.0
        for c in caps:
            i=(vP-c[0])/c[2]; c[0]=c[0]+i/c[1]*dt; ib=ib+i
        iK+=(vP-vS-iK*Rd1)/Lbank*dt
        vP+=(iF-ib-iK-iD2)/Cc*dt
        # eFuse + output loop
        if True:
            newdet=(state==0)&(iO>I_scp); tdet[newdet]=t; state[newdet]=1
            go=(state==1)&(t-tdet>=t_resp); tramp[go]=t; i_at[go]=iO[go]; state[go]=2
            hold=(state==2)&(t-tramp>=t_ramp); state[hold]=3
            cl=(state==3)&(t-tramp>=t_ramp+t_hold); state[cl]=4
            # current the eFuse can carry
            lim=np.where(state<=1,np.inf,np.where(state==2,i_at*np.clip(1-(t-tramp)/t_ramp,0,1),np.where(state==3,0.0,I_ol)))
            if ipk_cap is not None: lim=np.minimum(lim,ipk_cap)
            # output loop: try conducting through the eFuse (Ron) into the short
            diO_on=(vS-iO*(Ron+Rd2))/Ls
            iO_try=iO+diO_on*dt
            thru=iO_try<=lim
            # if the eFuse limits, OUT falls; Schottky clamps OUT at -v_sch: loop current decays through Rd2 + Schottky
            diO_sch=(-v_sch-iO*(Rd2+r_sch))/Ls
            iO_new=np.where(thru,iO_try,np.maximum(iO+diO_sch*dt,np.minimum(lim,iO_try)))
            ief=np.where(thru,iO_new,np.minimum(lim,iO_new))
            isch=np.maximum(iO_new-ief,0)
            # Pass 6 m2: OUT = -(Vf0 + r_dyn x I) while the Schottky carries the loop (MDD SS310B Fig. 3: ~1.15 V @ 10 A, ~1.35 V @ 20 A)
            vout=np.where(thru,iO_new*Rd2,np.where(iO_new>ief+1e-9,-(v_sch+r_sch*isch),iO_new*Rd2))
            iO=iO_new
        iDin=tvs_i(vS,tvs_in,n_slot) if tvs_in else 0.0*vS
        vS+=(iK-ief-iDin)/Cs*dt
        E_ef+=np.maximum(vS-vout,0)*ief*dt; E_sch+=isch*v_sch*dt; E_bank+=iK*iK*0.0035*dt; I2t+=iL*iL*dt
        vU+=(np.maximum(vP-0.45-vU,0)/r_u65-i_u65)/10e-6*0.75*dt
        vov=vB/OV_RATIO
        newt=(vov>vovr)&~np.isfinite(trip); trip[newt]=t
        trip[(vov<1.091)&np.isfinite(trip)&(t-trip<tdeg)]=np.inf
        fire=np.isfinite(trip)&(t-trip>=tdeg+hgate_extra)&~np.isfinite(qoff); qoff[fire]=t; tripped|=fire
        for k_,v_ in (('vP',vP),('vB',vB),('vS',vS),('vU',vU),('ief',ief),('iK',iK),('iL',iL)): pk[k_]=np.maximum(pk[k_],v_)
        pk['vout_neg']=np.minimum(pk['vout_neg'],vout)
        t_ovp+=(vS>ovp_min)*dt; vS_lo=np.minimum(vS_lo,vS)
        t+=dt
    return dict(pk=pk,E_ef=E_ef,E_sch=E_sch,E_bank=E_bank,I2t=I2t,tripped=tripped,t_ovp=t_ovp,vS_lo=vS_lo)

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
    print('PART 1 (historical, Pass 4 slot = TPS48100 latch; superseded by PART 2 in Pass 5)')
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

def ef_one(a):
    V,cs,lb,tr,cap=a
    r=run_ef(V,Cs_slot=cs,Lbank=lb,t_resp=tr,ipk_cap=cap,T=60e-6,dt=2e-9); p=r['pk']
    return a,dict(vP=p['vP'].max(),vB=p['vB'].max(),vS=p['vS'].max(),vU=p['vU'].max(),ief=p['ief'].max(),iL=p['iL'].max(),trip=int(r['tripped'].sum()),
                  I2t=r['I2t'].max(),vneg=p['vout_neg'].min(),Eef=r['E_ef'].max(),tovp=r['t_ovp'].max(),vSlo=r['vS_lo'].min())
def hp_one(a):
    lab,kw=a; r=hotplug(32.0,cgd=200e-12,T=120e-3,**kw); return a,r,soa_check(r['vds'],r['iD'])
if __name__=='__main__':
    print('\n\nPART 2 - Pass 5 design (Ethan 2026-11-23): slots on TPS16630 eFuses (2.2 uF/100 V IN cap, SS310B OUT->GND), U1 HGATE 22 nF + 1k,')
    print('47R ahead of C225/U65, C602 1 uF + Q2 hold-off on U2 EN/UVLO (Pass 6). Grid: 16 corners above x Lbank 60/150 nH (bank FETs + shunt + backplane) x eFuse')
    print('response 1.0/1.5 us. "pessimistic" = current rises freely until the SCP turn-off (no FET saturation); "realistic" = FET saturates at 60 A.')
    import multiprocessing as mp, itertools
    jobs=list(itertools.product((24.0,28.8,32.0),(2.2e-6,),(60e-9,150e-9),(1.0e-6,1.5e-6),(None,60.0)))
    with mp.Pool(min(8,mp.cpu_count())) as P: R=P.map(ef_one,jobs)
    print('%-5s %-12s %7s %7s %10s %6s %8s %8s %6s %9s %7s %7s'%('Vbat','case','VBAT_P','BAT_IN','VBAT_SLOTS','U65','eFuse pk','harness','OVtrip','F1 I2t','OUT min','t>OVP'))
    W={}
    for V in (24.0,28.8,32.0):
        for cap,lab in ((None,'pessimistic'),(60.0,'realistic')):
            rr=[r for a,r in R if a[0]==V and a[4]==cap]
            w={k:(min if k in ('vneg','vSlo') else max)(x[k] for x in rr) for k in rr[0]}; W[(V,lab)]=w
            print('%-5.1f %-12s %6.1fV %6.1fV %9.1fV %5.1fV %7.0fA %7.0fA %3d/%-3d %8.4f %6.2fV %5.1fus'%(V,lab,w['vP'],w['vB'],w['vS'],w['vU'],w['ief'],w['iL'],w['trip'],16*len(rr),w['I2t'],w['vneg'],w['tovp']*1e6))
    p32=W[(32.0,'pessimistic')]
    print('\nAbs-max check at the worst corner (32 V, pessimistic):')
    for part,v,lim in (('U1 LM74800 A (BAT_IN)',p32['vB'],70),('C297 100 V (BAT_IN)',p32['vB'],100),('U2 LM5176 VIN (VBAT_P)',p32['vP'],60),('U68 TPS1HTC30 VS (VBAT_P)',p32['vP'],64),
                       ('U5 LMR36506 VIN (VBAT_P)',p32['vP'],70),('C3/C4 63 V electrolytic (VBAT_P)',p32['vP'],63),('TPS16630 IN, all slots (VBAT_SLOTS)',p32['vS'],67),
                       ('U110 TPS48100 CS+/VS (VBAT_P), SRC (VBAT_SLOTS)',max(p32['vP'],p32['vS']),100),('card SLn_VBAT parts via healthy slots: SI2309CDS DI-8 (VBAT_SLOTS, us)',p32['vS'],60),
                       ('U65 TPS7B6950 IN',p32['vU'],45)):
        print('  %-52s %5.1f V vs %3d V  margin %5.1f V (%3.0f %%)'%(part,v,lim,lim-v,100*(lim-v)/lim))
    print('  healthy-slot OVP: VBAT_SLOTS above the 53.4 V OVP minimum for <= %.1f us << OVP_toff 8.5 us min: no nuisance trip'%(p32['tovp']*1e6))
    print('  faulted-slot OUT: SS310B clamps it at %.2f V (pessimistic) / %.2f V (realistic) for about 1 us (Vf 1.2 V + 20 mOhm, MDD Fig. 3). That is below the'%(p32['vneg'],W[(32.0,'realistic')]['vneg']))
    print('  -0.3 V OUT abs max for that time; TI SLVSET9G 9.4.1 anticipates this inductive negative spike and names the Schottky at OUT/GND as the remedy.')
    print('  Card-side SLn_VBAT parts (netlist, Pass 6 m1): DI-8 SI2309CDS 60 V (tightest), HSO-5/BRK-4 TPS1HTC30 VS 64 V (81 V < 100 us), AI-4 BCP56 80 V,')
    print('  card caps 100 V. There is no LM5176 on any card.')
    print('  VBAT_SLOTS minimum in the pessimistic corner %.1f V is a lumped-model artefact (the healthy slots\' card capacitors back-feed through their'%p32['vSlo'])
    print('  ON eFuses and are not modelled); realistic corner >= %.1f V; healthy-slot UVLO has a 100 us RC and a 9-16 us deglitch.'%min(W[(V,'realistic')]['vSlo'] for V in (24.0,28.8,32.0)))
    print('\nHot-plug / power-up at 32 V, Q2 turn-on (Cgd 200 pF corner), Tc 149 F (65 C); load = U2 LM5176 70 W out (eta 0.88) starting at its')
    print('EN/UVLO threshold and ramping over the 7.5 ms soft start (linear in time). SOA = worst sliding window vs BSC070 Diagram 3 derated to Tc 65 C.')
    HP=[('as built: no CdVdT, U2 load',dict(c_dvdt=0.0,ihg=75e-6,p_load=70.0,dt=5e-9)),
        ('as built: no CdVdT, U2 load, HGATE 39 uA',dict(c_dvdt=0.0,ihg=39e-6,p_load=70.0,dt=5e-9)),
        ('22 nF + 1k, U2 starts at 4.96 V (no C602)',dict(c_dvdt=22e-9,ihg=39e-6,p_load=70.0,dt=5e-8)),
        ('22 nF + 1k, U2 starts at 4.96 V, HGATE 75 uA',dict(c_dvdt=22e-9,ihg=75e-6,p_load=70.0,dt=5e-8)),
        ('10 nF + 1k, U2 starts at 4.96 V',dict(c_dvdt=10e-9,ihg=75e-6,p_load=70.0,dt=5e-8)),
        ('Pass 5: 22 nF + 1k + C602 10 uF (5 uF eff), HGATE 39 uA',dict(c_dvdt=22e-9,ihg=39e-6,p_load=70.0,c_uvlo=5e-6,dt=5e-8)),
        ('Pass 5: 22 nF + 1k + C602 10 uF (5 uF eff), HGATE 75 uA',dict(c_dvdt=22e-9,ihg=75e-6,p_load=70.0,c_uvlo=5e-6,dt=5e-8)),
        ('22 nF + 1k, U2 and U5 held off (Pass 6 hold-off), HGATE 39 uA',dict(c_dvdt=22e-9,ihg=39e-6,dt=5e-8)),
        ('22 nF + 1k, U2 and U5 held off (Pass 6 hold-off), HGATE 75 uA',dict(c_dvdt=22e-9,ihg=75e-6,dt=5e-8))]
    with mp.Pool(min(8,mp.cpu_count())) as P: H=P.map(hp_one,HP)
    for (lab,kw),r,sc in H:
        st=('U2 starts %.0f ms (after the ramp)'%(r['t_on_pred']*1e3)) if r.get('t_on_pred') else (('U2 starts %.1f ms'%(r['t_on']*1e3)) if r['t_on'] else 'no load')
        print('  %-56s pk %5.1f A, Q2 dTj %3.0f K -> Tj %3.0f F (%3.0f C), ramp %4.1f ms, %-30s SOA %.2f (%s)'%(lab,r['ipk'],r['dTj'],F(65+r['dTj']),65+r['dTj'],r['t']*1e3,st,sc[0],
              'OK' if sc[0]<=1 else 'EXCEEDED'))
    print('  Pass 6 B1: the Q2 hold-off (BAT_IN - VBAT_P > 2.5-3.8 V) now keeps U2 and U5 off during the ramp, and C602 is 1 uF (was 10 uF) so the')
    print('  hold-off can stop U2 within 0.25 ms on a warm restart. Cold start, warm restart and all corners: docs/modular/pass6_fix_calc.txt.')
