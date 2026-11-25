#!/usr/bin/env python3
"""Shared ngspice deck builder for the M7 power front end (both branches).
Netlist facts (kicad-cli netlist of genctl.kicad_sch, 2026-11-24):
  BAT_IN: C297 220n, D1 SMDJ40CA, D401 1N4148W, U1 A, OV divider R1 210k / R2 49.9k / R3 8.66k.
  Q1 BSC070N10NS5 (S = BAT_IN, G = DGATE, D = VBAT_DD); VBAT_DD: C1, C2 100n; Q2 BSC070N10NS5 (D = VBAT_DD, G = HGATE,
  S = VBAT_PS) -> R555 2 mOhm -> VBAT_P. U1 HGATE -> R1001 1k -> C601 (drawn 22n/100 V before this SPICE pass, now 100n/100 V).
  VBAT_P: C5-C8 4x10u X7S, C38 2.2u, C39/C233 100n, C3/C4 2x EEETG1J101UP 100u 63 V (0.8 Ohm), D2 SMBJ40CA,
  modular + C1105 2.2u/100 V; split + 15x100n (C205-C219). U65 feed D120 SS110 + C225 10u (modular adds R1002 47R ahead).
  Hold-off (both): D401 1N4148W, Q121 MMBT5401, R1121 22k, R1122 68k, R1123 22k, C1121 100n, R1124 100k, Q122 MMBT3904,
  D402 BAT54C (pin 1 BB_UVLO, pin 2 U5_EN, pin 3 HO_K). U2 EN/UVLO = BB_UVLO: R4 100k / R5 33k, C602 1u.
  U5 EN: R1125 100k / R1126 47k from VBAT_P.
Vendor models: Infineon BSC070N10NS5 (OptiMOS5_100V_Spice.lib, with the thermal Tj/Tcase nodes), TI TPS48100-Q1 (SLUM908).
Behavioral (models/behav.lib): LM74800, TPS16630, TVS, U2 and U5 as loads. Small parts: models/small.lib.
"""
import os, subprocess, tempfile, numpy as np, sys, math, re
HERE=os.path.dirname(os.path.abspath(__file__))
F=lambda c: c*9/5+32
# C601 (U1 HGATE dV/dt cap via R1001 1k): drawn 22 nF; SPICE finding -> 100 nF (CL10B104KC8NNNC, C15725). Decks use this unless p['c601'].
C601_DEFAULT=100e-9
# kick_calc TVS dict (VBR_max, VC, Ipp) -> rd
TVS={'SMDJ40CA':(49.1,(64.5-49.1)/46.5),'SMBJ40CA':(49.1,(64.5-49.1)/9.3)}

def frontend(p):
    """p: dict. V, Rb, Lb, cold, ihg, tdeg, branch ('mod'|'split'), vb_src (netlist line for the battery source or None),
    holdoff (bool), u2 (None|dict), u5 (None|dict), c602 (F), temp (C), ride (None|dict option)."""
    cold=p.get('cold',False); br=p.get('branch','mod')
    L=[]
    L.append('.include %s/models/OptiMOS5_100V_Spice.lib'%HERE)
    L.append('.include %s/models/behav.lib'%HERE)
    L.append('.include %s/models/small.lib'%HERE)
    L.append(p.get('vb_src') or 'Vbat vb 0 DC %g'%p['V'])
    if p.get('bat_switch'):           # battery interruption: series switch, control node bsw (1 = closed)
        L.append('Rb vb nb1 %g'%p['Rb']); L.append('Bsbat nb1 nb I = V(nb1,nb)*exp(6.9078*max(min(V(bsw),1),0)-18.4207*(1-max(min(V(bsw),1),0)))')   # log-linear 1e-8..1e3 S
        L.append('Cnb nb nbc 47n'); L.append('Rnb nbc 0 2')   # harness-side snubber (cable capacitance + damping): gives Lb's current a path when the switch opens
    else:
        L.append('Rb vb nb %g'%p['Rb'])
    L.append('Lb nb BAT_IN %g'%p['Lb'])
    if p.get('bat_short'):            # BAT_IN pulled to ground (crank-type dip): control node bsh (1 = shorted)
        L.append('Bsbsh BAT_IN bshn I = V(BAT_IN,bshn)*exp(6.9078*max(min(V(bsh),1),0)-18.4207*(1-max(min(V(bsh),1),0)))'); L.append('Rbsh bshn 0 %g'%p.get('r_short',0.05))
    L.append('C297 BAT_IN 0 %g'%(0.22e-6*0.8+0.05e-6))
    L.append('XD1 BAT_IN 0 TVSCA PARAMS: vbr=%g rd=%g'%TVS['SMDJ40CA'])
    L.append('R1 BAT_IN UVLO 210k'); L.append('R2 UVLO OV 49.9k'); L.append('R3 OV 0 8.66k')
    L.append('Vtc tc 0 %g'%p.get('tcase',65.0))
    zt=p.get('zthtype',1)
    L.append('XQ1 VBAT_DD DGATE BAT_IN tj1 tc BSC070N10NS5 PARAMS: Zthtype=%d'%zt)
    L.append('C1 VBAT_DD 0 80n'); L.append('C2 VBAT_DD 0 80n')
    L.append('VQ2 VBAT_DD q2d 0')
    L.append('XQ2 q2d HGATE VBAT_PS tj2 tc BSC070N10NS5 PARAMS: Zthtype=%d'%zt)
    L.append('R555 VBAT_PS vp1 2m'); L.append('Lf vp1 VBAT_P 10n')
    fon=p.get('force_on', p.get('vb_src') is None)   # running-state decks (DC battery) start with U1 enabled
    L.append('XU1 BAT_IN VBAT_DD DGATE HGATE VBAT_P OV UVLO LM74800B PARAMS: ihg=%g tdeg=%g fon=%d'%(p.get('ihg',75e-6),p.get('tdeg',3.98e-6),1 if fon else 0))
    L.append('R1001 HGATE DVDT 1k'); L.append('C601 DVDT 0 %g'%p.get('c601',C601_DEFAULT))
    # VBAT_P ceramics (bias derating as kick_calc) + bulk electrolytics
    cc=(4*10e-6*0.55+2.2e-6*0.5) if cold else (4*10e-6*0.65+2.2e-6*0.6)
    cc+=0.2e-6
    if br=='mod': cc+=2.2e-6*(0.5 if cold else 0.6)          # C1105
    else: cc+=15*0.1e-6*0.63                                  # C205-C219
    L.append('CC VBAT_P 0 %g'%cc)
    ce,ee=(80e-6,3.2) if cold else (100e-6,0.8)
    for k in (3,4): L.append('C%d c%de 0 %g'%(k,k,ce)); L.append('RC%d VBAT_P c%de %g'%(k,k,ee))
    L.append('XD2 VBAT_P 0 TVSCA PARAMS: vbr=%g rd=%g'%TVS['SMBJ40CA'])
    # U65 feed (TPS7B6950, 45 V abs max)
    if br=='mod': L.append('R1002 VBAT_P u65a 47'); L.append('D120 u65a U65_IN DSS110')
    else: L.append('D120 VBAT_P U65_IN DSS110')
    L.append('C225 U65_IN 0 7.5u'); L.append('B65 U65_IN 0 I = 5m*0.5*(1+tanh((V(U65_IN)-1)/0.3))')
    # U2 EN/UVLO, U5 EN, hold-off
    L.append('R4 VBAT_P BB_UVLO 100k'); L.append('R5 BB_UVLO 0 33k'); L.append('C602 BB_UVLO 0 %g'%p.get('c602',1e-6))
    u5en_src=p.get('u5en_src','VBAT_P')
    L.append('R1125 %s U5_EN 100k'%u5en_src); L.append('R1126 U5_EN 0 47k')
    if p.get('holdoff',True):
        L+=['D401 BAT_IN ho_a D1N4148','Q121 ho_c ho_b ho_a Q2N5401','R1121 ho_a ho_b 22k','R1122 ho_b VBAT_P 68k',
            'R1123 ho_c HO_F 22k','C1121 HO_F 0 100n','R1124 HO_F 0 100k','Q122 HO_K HO_F 0 Q2N3904','D402A BB_UVLO HO_K DBAT54']
        if p.get('u5_holdoff',True):
            L.append('D402B %s HO_K DBAT54'%p.get('u5_ho_node','U5_EN'))
    u2=p.get('u2')
    if u2 is not None:
        L.append('XU2 VBAT_P BB_UVLO U2LOAD PARAMS: pin=%g ilim=3.56 tss=7.5m ss0=%g'%(u2.get('pin',79.5),u2.get('ss0',0)))
    u5=p.get('u5')
    if u5 is not None:
        L.append('XU5 %s U5_EN U5_ALIVE U5LOAD PARAMS: p=%g von=%g voff=%g'%(u5.get('vin','VBAT_P'),u5.get('p',2.1),u5.get('von',1.26),u5.get('voff',1.16)))
    for x in p.get('extra',[]): L.append(x)
    return L

def run(lines, probes, tstop, tstep, name, tmax=None, temp=None, ic=None, opts='', uic=False, keep=False, timeout=1200, nodeset=None):
    """Run a transient; probes = list of ngspice vector expressions. Returns dict name->array, plus 't'."""
    wd=os.path.join(HERE,'work'); os.makedirs(wd,exist_ok=True)
    cir=os.path.join(wd,name+'.cir'); out=os.path.join(wd,name+'.dat')
    hdr=['* '+name]+lines
    if temp is not None: hdr.append('.temp %g'%temp)
    if ic: hdr.append('.ic '+' '.join('V(%s)=%g'%(k,v) for k,v in ic.items()))
    if nodeset: hdr.append('.nodeset '+' '.join('V(%s)=%g'%(k,v) for k,v in nodeset.items()))
    hdr.append('.options method=gear reltol=1e-3 abstol=1e-9 vntol=1e-5 itl4=200 '+opts)
    hdr.append('.tran %g %g 0 %g%s'%(tstep,tstop,tmax or tstep,' uic' if uic else ''))
    hdr+=['.control','set wr_singlescale','set wr_vecnames','option numdgt=7','run',
          'wrdata %s %s'%(out,' '.join(probes)),'.endc','.end']
    open(cir,'w').write('\n'.join(hdr)+'\n')
    r=subprocess.run(['ngspice','-b',cir],capture_output=True,text=True,timeout=timeout,cwd=HERE)
    if not os.path.exists(out) or os.path.getmtime(out)<os.path.getmtime(cir):
        raise RuntimeError('ngspice failed for %s:\n%s'%(name,(r.stdout+r.stderr)[-3000:]))
    with open(out) as f: head=f.readline().split()
    d=np.loadtxt(out,skiprows=1,ndmin=2)
    res={'t':d[:,0]}
    for i,h in enumerate(head[1:],1): res[probes[i-1]]=d[:,i]
    if 'aborted' in r.stdout or 'too small' in r.stdout:
        res['_warn']='aborted at t=%g'%d[-1,0]
    if not keep:
        try: os.remove(out)
        except OSError: pass
    return res

# SOA check identical to the hand calc (kick_calc.soa_check, BSC070N10NS5 Diagram 3 derated to Tc 149 F / 65 C)
from soa import soa_check, soa_i

def resample(t,y,dt,t0=None,t1=None):
    t0=t[0] if t0 is None else t0; t1=t[-1] if t1 is None else t1
    n=max(1,int((t1-t0)/dt)); edges=t0+dt*np.arange(n+1)
    # bin averages with trapezoid integration
    cy=np.concatenate([[0],np.cumsum(0.5*(y[1:]+y[:-1])*np.diff(t))]); ct=t
    Y=np.interp(edges,ct,cy); return np.diff(Y)/dt

def soa(res,dt=1e-5,t0=None,t1=None,vds='v(VBAT_DD,VBAT_PS)',idr='i(VQ2)'):
    t=res['t']; v=np.maximum(res[vds],0); i=np.maximum(res[idr],0)
    p=v*i
    P=resample(t,p,dt,t0,t1); I=resample(t,i,dt,t0,t1)
    V=np.where(I>1e-6,P/np.maximum(I,1e-9),0)
    return soa_check(V,I,Tc=65.0,dt=dt)

def integ(t,y,t0=None,t1=None):
    m=np.ones_like(t,bool)
    if t0 is not None: m&=t>=t0
    if t1 is not None: m&=t<=t1
    return float(np.trapezoid(y[m],t[m]))

def first(t,cond):
    idx=np.nonzero(cond)[0]
    return float(t[idx[0]]) if len(idx) else None

def ns_on(V,br='mod'):
    """nodeset for a running front end at battery V"""
    d=dict(BAT_IN=V,VBAT_DD=V,VBAT_PS=V,VBAT_P=V,HGATE=V+11.3,DVDT=V+11.3,DGATE=V+11,BB_UVLO=V*33/133,U5_EN=V*47/147,HO_F=0,
           HO_K=min(V*33/133,V*47/147),UVLO=V*58.56/268.56,OV=V/31.01,U65_IN=V-0.6,VBAT_SLOTS=V,OUT=V,efin=V)
    return d
