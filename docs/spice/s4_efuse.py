#!/usr/bin/env python3
"""Sim 4 (modular): TPS16630 slot eFuse at R_ILIM 3.09k (I_OL 5.36-6.30 A), behavioral (TI's TPS1663 model is encrypted).
Slot 1 faulted; slot 2 modelled explicitly as a healthy card (its own TPS16630, card caps 22 uF, 3 A resistive load); slots 3-8
lumped as their input caps + 3 A each. Bank = Lbank 60 nH + 10 mOhm; front end as fe.frontend (vendor BSC070 Q1/Q2), U2 at full load,
U5 2.1 W, hold-off in. Harness Rb 15 mOhm / Lb 0.5 uH (fast corner) and Rb 35 mOhm / Lb 2 uH (slow corner).
 (a) hard short on slot 1 (Ls 50 nH, Rd2 12 mOhm), pessimistic (no FET saturation), t_resp 1.5 us;
 (b) overload on slot 1: load steps from 3 A to 8 A (resistive) -> eFuse regulates at I_OL;
 (c) what the 22 nF HGATE cap (C601 via R1001 1k) and R1002 47R do in these events: Q2 gate and U65 input.
Usage: s4_efuse.py -> results/s4_efuse_mod.txt"""
import sys, numpy as np, os, multiprocessing as mp
from fe import *
T_EV=20e-6
def deck(V,case,slow,iol):
    Rb,Lb=(0.035,2e-6) if slow else (0.015,0.5e-6)
    p=dict(V=V,Rb=Rb,Lb=Lb,branch='mod',u2=dict(ss0=1),u5=dict())
    L=frontend(p)
    L.insert(0,'.include %s/models/efuse_ol.lib'%HERE)
    cs=6*(2.2e-6*0.6+0.1e-6*0.63)+2.2e-6*0.6+0.1e-6*0.63
    L+=['Lbank VBAT_P bk1 60n','Rd1 bk1 VBAT_SLOTS 10m','CS VBAT_SLOTS 0 %g'%cs,'RS38 VBAT_SLOTS 0 %g'%(V/18.0),
        # slot 2 healthy
        'CS2 VBAT_SLOTS 0 %g'%(2.2e-6*0.6+0.1e-6*0.63),'VEF2 VBAT_SLOTS ef2 0','XEF2 ef2 OUT2 TPS16630OL PARAMS: iol=%g'%iol,'DS2 0 OUT2 DSS310',
        'Lc2 OUT2 card2 50n','Ccard2 card2 0 22u','Rcard2 card2 0 %g'%(V/3.0),
        # slot 1 faulted
        'CS1 VBAT_SLOTS 0 %g'%(2.2e-6*0.6+0.1e-6*0.63),'VEF VBAT_SLOTS efin 0','XEF efin OUT TPS16630OL PARAMS: tresp=1.5 iol=%g'%iol,'DSCH 0 OUT DSS310',
        'Ls OUT ls1 50n','Ccard1 ls1 0 22u','Rload1 ls1 0 %g'%(V/3.0)]
    if case=='short':
        L+=['Rd2 ls1 ls2 12m','Bsh ls2 0 I = V(ls2)*(1e3*max(min(V(shc),1),0)+1e-9)','Vsh shc 0 PWL(0 0 %g 0 %g 1)'%(T_EV,T_EV+1e-9)]
    else:
        R8=V/8.0; Rx=1/(1/R8-1/(V/3.0))
        L+=['Rx ls1 ls2 %g'%Rx,'Bsh ls2 0 I = V(ls2)*(1e3*max(min(V(shc),1),0)+1e-9)','Vsh shc 0 PWL(0 0 %g 0 %g 1)'%(T_EV,T_EV+1e-6)]
    return L
PR=['v(VBAT_P)','v(BAT_IN)','v(VBAT_SLOTS)','i(VEF)','i(VEF2)','v(OUT)','v(OUT2)','v(card2)','v(U65_IN)','v(HGATE,VBAT_P)','v(xu1.offs)','v(tj2)','v(ls1)']
def one(a):
    V,case,slow,iol=a
    ns=ns_on(V); ns.update(OUT=V,OUT2=V,card2=V,ef2=V,ls1=V)
    tst=150e-6 if case=='short' else 3e-3
    r=run(deck(V,case,slow,iol),PR,tst,2e-9 if case=='short' else 20e-9,'s4_%g_%s_%d_%g'%(V,case,slow,iol),tmax=5e-9 if case=='short' else 0.2e-6,nodeset=ns)
    t=r['t']; m=t>T_EV
    ief=r['i(VEF)']; vs=r['v(VBAT_SLOTS)']
    d=dict(a=a,vP=float(r['v(VBAT_P)'][m].max()),vB=float(r['v(BAT_IN)'][m].max()),vS=float(vs[m].max()),vSlo=float(vs[m].min()),
           ief=float(ief[m].max()),ief_end=float(np.mean(ief[t>t[-1]-20e-6])),
           i2min=float(r['i(VEF2)'][m].min()),i2max=float(r['i(VEF2)'][m].max()),card2min=float(r['v(card2)'][m].min()),out2min=float(r['v(OUT2)'][m].min()),
           vU=float(r['v(U65_IN)'][m].max()),ov=bool(r['v(xu1.offs)'].max()>0.5),hg_min=float(r['v(HGATE,VBAT_P)'][m].min()),
           tovp=float(np.trapezoid((vs>53.4).astype(float),t)),outmin=float(r['v(OUT)'][m].min()),
           vout_end=float(np.mean(r['v(ls1)'][t>t[-1]-20e-6])),pef_end=float(np.mean((vs-r['v(OUT)'])[t>t[-1]-20e-6]*ief[t>t[-1]-20e-6])),warn=r.get('_warn'))
    # time for the overload to settle within 5 % of I_OL
    if case=='overload':
        k=np.nonzero(m&(np.abs(ief-iol)>0.05*iol))[0]; d['tset']=float(t[k[-1]]-T_EV) if len(k) else 0.0
    return d
if __name__=='__main__':
    jobs=[(V,c,s,iol) for V in (24.0,32.0) for c in ('short','overload') for s in (0,1) for iol in ((6.30,) if c=='short' else (5.36,6.30))]
    with mp.Pool(8) as P: R=P.map(one,jobs,chunksize=1)
    out=[__doc__,'']
    out.append('(a) hard short on slot 1')
    out.append('Vb   harness | eFuse pk  VBAT_P  BAT_IN  VBAT_SLOTS max/min  t>53.4V OVP | slot 2: eFuse I min/max  card V min  OUT2 min | U65 IN  OV trip  Q2 Vgs min')
    for x in R:
        V,c,s,iol=x['a']
        if c!='short': continue
        out.append('%4.1f %-7s | %6.0f A  %5.1f V  %5.1f V  %5.1f / %5.1f V  %5.2f us  | %6.1f / %5.1f A        %5.1f V   %5.1f V | %5.1f V  %-5s  %5.2f V'%(
            V,'slow' if s else 'fast',x['ief'],x['vP'],x['vB'],x['vS'],x['vSlo'],x['tovp']*1e6,x['i2min'],x['i2max'],x['card2min'],x['out2min'],x['vU'],x['ov'],x['hg_min']))
    out.append('\n(b) overload on slot 1 (3 A -> 8 A resistive)')
    out.append('Vb   harness I_OL  | eFuse pk  settles to       within 5 %% after  eFuse power  OUT V | VBAT_SLOTS min  slot 2 card min | VBAT_P max')
    for x in R:
        V,c,s,iol=x['a']
        if c!='overload': continue
        out.append('%4.1f %-7s %4.2f | %6.2f A  %5.2f A  %8.0f us   %6.1f W   %5.1f V | %6.1f V        %6.1f V        | %5.1f V'%(
            V,'slow' if s else 'fast',iol,x['ief'],x['ief_end'],x['tset']*1e6,x['pef_end'],x['vout_end'],x['vSlo'],x['card2min'],x['vP']))
    w=[x for x in R if x['warn']]; out.append('\nSimulator warnings: %d'%len(w))
    txt='\n'.join(out); print(txt); open(os.path.join(HERE,'results','s4_efuse_mod.txt'),'w').write(txt+'\n')
