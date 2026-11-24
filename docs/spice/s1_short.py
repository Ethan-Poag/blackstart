#!/usr/bin/env python3
"""Sim 1 (modular): dead short at one slot output, downstream of the bank switch (U110) and Q2.
Same grid as kick_calc PART 2: Rb 15/35 mOhm x Lb 0.5/2 uH x Rd2 12/25 mOhm x caps nominal/cold-aged x Lbank 60/150 nH x
eFuse response 1.0/1.5 us; 'pessimistic' = eFuse current rises freely until the SCP turn-off, 'realistic' = FET saturates at 60 A.
Slot network as kick_calc: bank = Lbank + Rd1 10 mOhm (bank FETs, 5 mOhm shunt, backplane); VBAT_SLOTS = 8 x (2.2 uF/100 V X7R
+ 100 nF) + C413 2.2u + 100 nF lumped; faulted slot TPS16630 (behavioral) -> OUT (SS310B to GND) -> Ls 50 nH -> Rd2 -> short.
Default: no load current (worst case for the kick, as the hand calc); 'load' = U2 at full load + U5 2.1 W (worst case for dips); the Q2 hold-off, LM74800 OV (behavioral) and vendor BSC070 Q1/Q2 are in the deck.
Usage: s1_short.py mod [load] -> results/s1_short_mod[_load].txt"""
import sys, itertools, multiprocessing as mp, numpy as np
from fe import *
T_SH=2e-6
def deck(V,Rb,Lb,Rd2,cold,Lbank,tresp,isat,br='mod',bankmode='lumped',load=False):
    p=dict(V=V,Rb=Rb,Lb=Lb,cold=cold,branch=br,u2=dict(ss0=1) if load else None,u5=dict() if load else None)
    L=frontend(p)
    cs=8*(2.2e-6*(0.5 if cold else 0.6)+0.1e-6*0.63)+2.2e-6*(0.5 if cold else 0.6)+0.1e-6*0.63
    L+=['Lbank VBAT_P bk1 %g'%Lbank,'Rd1 bk1 VBAT_SLOTS 10m','CS VBAT_SLOTS 0 %g'%cs,
        'VEF VBAT_SLOTS efin 0','XEF efin OUT TPS16630B PARAMS: ron=19m iscp=45 tresp=%g iol=6.30 isat=%g'%(tresp,isat),
        'DSCH 0 OUT DSS310','ROUT OUT 0 1k','Ls OUT ls1 50n','Rd2 ls1 ls2 %g'%Rd2,'Ssh ls2 0 shc 0 SWSH',
        '.model SWSH SW(Ron=1m Roff=1G Vt=0.5 Vh=0.1)','Vsh shc 0 PWL(0 0 %g 0 %g 1)'%(T_SH,T_SH+1e-9)]
    return L
PROBES=['v(xu1.uvs)','v(xu1.ovs)','v(BB_UVLO)','v(U5_EN)','v(HGATE,VBAT_P)','v(BAT_IN)','v(VBAT_P)','v(VBAT_SLOTS)','v(U65_IN)','i(VEF)','i(Lb)','v(OUT)','v(VBAT_DD,VBAT_PS)','i(VQ2)','v(tj2)','v(tj1)','v(xu1.offs)','v(HO_F)']
LOAD=False
def one(a):
    V,Rb,Lb,Rd2,cold,Lbank,tresp,case=a
    isat=60.0 if case=='realistic' else 1e6
    name='s1%s_%g_%g_%g_%g_%d_%g_%g_%s'%('L' if LOAD else '',V,Rb*1e3,Lb*1e6,Rd2*1e3,cold,Lbank*1e9,tresp,case[0])
    r=run(deck(V,Rb,Lb,Rd2,cold,Lbank,tresp,isat,load=LOAD),PROBES,80e-6,2e-9,name,tmax=5e-9,nodeset=ns_on(V))
    t=r['t']; vds=r['v(VBAT_DD,VBAT_PS)']; iq=r['i(VQ2)']
    m=t>=T_SH
    tv=lambda k,s=1: float((s*r[k][m]).max()*s)
    v1,r1=TVS['SMDJ40CA']; v2,r2=TVS['SMBJ40CA']
    vb=r['v(BAT_IN)']; vp=r['v(VBAT_P)']
    eD1=integ(t,vb*np.maximum(vb-v1,0)/r1); eD2=integ(t,vp*np.maximum(vp-v2,0)/r2)
    ief=r['i(VEF)']
    # eFuse trip time: from short to the eFuse current first falling below 10 A after its peak
    kpk=np.argmax(ief); tt=first(t[kpk:],ief[kpk:]<10.0)
    return dict(a=a,vP=tv('v(VBAT_P)'),vB=tv('v(BAT_IN)'),vS=tv('v(VBAT_SLOTS)'),vSlo=tv('v(VBAT_SLOTS)',-1),vU=tv('v(U65_IN)'),
                ief=float(ief.max()),iL=float(r['i(Lb)'].max()),vneg=float(r['v(OUT)'][m].min()),
                ov=bool(r['v(xu1.offs)'].max()>0.5),tj2=float(r['v(tj2)'].max()),tj1=float(r['v(tj1)'].max()),
                eq2=integ(t,np.maximum(vds,0)*np.maximum(iq,0),T_SH),iq2=float(iq.max()),vds2=float(vds.max()),
                ttrip=(tt-T_SH) if tt else None,eD1=eD1,eD2=eD2,i2t=integ(t,r['i(Lb)']**2),
                tovp=float(np.trapezoid((r['v(VBAT_SLOTS)']>53.4).astype(float),t)),ho=float(r['v(HO_F)'].max()),warn=r.get('_warn'),
                vPmin=tv('v(VBAT_P)',-1),vBmin=tv('v(BAT_IN)',-1),uv=bool(r['v(xu1.uvs)'][m].min()<0.5),ovt=bool(r['v(xu1.ovs)'][m].max()>0.5),
                bbmin=tv('v(BB_UVLO)',-1),u5enmin=tv('v(U5_EN)',-1),hgmin=tv('v(HGATE,VBAT_P)',-1),hgend=float(r['v(HGATE,VBAT_P)'][-1]),
                t_u5en=float(np.trapezoid((r['v(U5_EN)'][m]<1.16).astype(float),t[m])),t_vp4=float(np.trapezoid((vp[m]<4.0).astype(float),t[m])))
if __name__=='__main__':
    br=sys.argv[1] if len(sys.argv)>1 else 'mod'
    LOAD=len(sys.argv)>2 and sys.argv[2]=='load'
    sfx='_load' if LOAD else ''
    Vs=[12.0,24.0,32.0]
    G=list(itertools.product([0.015,0.035],[0.5e-6,2e-6],[0.012,0.025],[0,1],[60e-9,150e-9],[1.0,1.5]))
    jobs=[(V,)+g+(c,) for V in Vs for c in ('pessimistic','realistic') for g in G]
    with mp.Pool(8) as P: R=P.map(one,jobs,chunksize=1)
    import pickle; os.makedirs(os.path.join(HERE,'results'),exist_ok=True)
    pickle.dump(R,open(os.path.join(HERE,'work','s1_%s%s.pkl'%(br,sfx)),'wb'))
    out=[__doc__,'','Worst of 64 corners per row (ngspice 44.2; vendor BSC070N10NS5 Q1/Q2 with thermal network Zthtype=1 (max), Tcase 149 F / 65 C).',
         'Vbat  case          VBAT_P  BAT_IN VBAT_SLOTS VS_min   U65  eFuse pk harness  trip us   OVtrip  Q2 Ipk  Q2 E    Q2 Tj max        E_D1  E_D2  F1 I2t  OUT min  t>OVP  HO_F max']
    for V in Vs:
        for c in ('pessimistic','realistic'):
            S=[x for x in R if x['a'][0]==V and x['a'][7]==c]
            mx=lambda k: max(x[k] for x in S)
            tr=[x['ttrip'] for x in S if x['ttrip'] is not None]
            out.append('%4.1f  %-12s %6.1fV %6.1fV %8.1fV %6.1fV %5.1fV %6.0fA %6.0fA %4.2f-%4.2f %3d/64 %6.0fA %5.1fmJ %4.0fF (%3.0fC) %5.1fmJ %4.1fmJ %6.4f %6.2fV %4.1fus %5.2fV'%(
                V,c,mx('vP'),mx('vB'),mx('vS'),min(x['vSlo'] for x in S),mx('vU'),mx('ief'),mx('iL'),min(tr)*1e6,max(tr)*1e6,sum(x['ovt'] for x in S),
                mx('iq2'),mx('eq2')*1e3,F(mx('tj2')),mx('tj2'),mx('eD1')*1e3,mx('eD2')*1e3,mx('i2t'),min(x['vneg'] for x in S),mx('tovp')*1e6,mx('ho')))
    out.append('\nDips (same corners): VBAT_P / BAT_IN minimum, LM74800 UVLO glitch (BAT_IN < 5.2 V), U5_EN below 1.16 V, BB_UVLO minimum, Q2 gate')
    out.append('Vbat  case          VBAT_P min  BAT_IN min  t(VBAT_P<4V)  U1 UVLO   U5_EN<1.16V (max time)  BB_UVLO min  Q2 Vgs min  Q2 Vgs end')
    for V in Vs:
        for c in ('pessimistic','realistic'):
            S=[x for x in R if x['a'][0]==V and x['a'][7]==c]
            out.append('%4.1f  %-12s %6.2f V    %6.2f V    %5.2f us     %2d/64     %2d/64 (%5.2f us)        %5.2f V      %5.2f V     %5.2f V'%(V,c,min(x['vPmin'] for x in S),
                min(x['vBmin'] for x in S),max(x['t_vp4'] for x in S)*1e6,sum(x['uv'] for x in S),sum(x['u5enmin']<1.16 for x in S),max(x['t_u5en'] for x in S)*1e6,
                min(x['bbmin'] for x in S),min(x['hgmin'] for x in S),min(x['hgend'] for x in S)))
    w=[x for x in R if x['warn']]
    out.append('\nSimulator warnings: %d of %d runs%s'%(len(w),len(R),(' e.g. '+str(w[0]['a'])+' '+w[0]['warn']) if w else ''))
    txt='\n'.join(out); print(txt); open(os.path.join(HERE,'results','s1_short_%s%s.txt'%(br,sfx)),'w').write(txt+'\n')
