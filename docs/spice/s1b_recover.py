#!/usr/bin/env python3
"""Sim 1b (modular): what happens AFTER the slot dead short in the two loaded corners (of 384, results/s1_short_mod_load.txt) where
Q2's gate had not recovered 80 us after the short (LM74800 OV trip at 32 V / UVLO glitch at 12 V, both only in the 'pessimistic'
no-saturation eFuse model). Same deck as s1_short.py 'load' (U2 79.5 W, U5 2.1 W, hold-off, vendor BSC070 Q1/Q2), run to 80 ms with a
coarser max step after the event; C601 100 nF (applied) and 22 nF (as drawn before) for comparison. Reports whether the MCU stays up
(U2 running or U5 running), U2/U5 drop-out times, Q2 SOA (hand-calc soa_check, 10 us bins) and Tj during the gate recovery.
Usage: s1b_recover.py -> results/s1b_recover_mod.txt"""
import sys, multiprocessing as mp, numpy as np, os
from fe import *
import s1_short as S
def one(a):
    corner,c601=a
    V,Rb,Lb,Rd2,cold,Lbank,tresp,case=corner
    L=S.deck(V,Rb,Lb,Rd2,cold,Lbank,tresp,1e6,load=True)
    L=[('C601 DVDT 0 %g'%c601) if l.startswith('C601 ') else l for l in L]
    name='s1b_%g_%g_%g_%g'%(V,Rd2*1e3,tresp,c601*1e9)
    r=run(L,['v(VBAT_P)','v(BAT_IN)','v(VBAT_DD,VBAT_PS)','i(VQ2)','v(tj2)','v(HGATE,VBAT_P)','v(xu2.runs)','v(U5_ALIVE)','v(xu1.offs)'],
          80e-3,20e-9,name,tmax=0.2e-6,nodeset=ns_on(V),timeout=6000)
    t=r['t']; m=t>S.T_SH
    alive=(r['v(U5_ALIVE)']>0.5)|(r['v(xu2.runs)']>0.5)
    f=lambda c: first(t[m],c[m])
    s=soa(r,t0=S.T_SH)
    return dict(a=a,dead=f(~alive),u2d=f(r['v(xu2.runs)']<0.5),u5d=f(r['v(U5_ALIVE)']<0.5),soa=s,tj=float(r['v(tj2)'].max()),
                vgs_on=f(r['v(HGATE,VBAT_P)']>8.0) if r['v(HGATE,VBAT_P)'][-1]>8 else None,vpmin=float(r['v(VBAT_P)'][m].min()),
                u2back=first(t[t>2e-3],r['v(xu2.runs)'][t>2e-3]>0.5),warn=r.get('_warn'))
if __name__=='__main__':
    C=[(12.0,0.015,2e-6,0.012,1,150e-9,1.5,'pessimistic'),(32.0,0.015,2e-6,0.025,1,60e-9,1.5,'pessimistic')]
    J=[(c,x) for c in C for x in (100e-9,22e-9)]
    with mp.Pool(4) as P: R=P.map(one,J,chunksize=1)
    out=[__doc__,'','Vb   corner (Rb, Lb, Rd2, cold, Lbank, tresp)   C601 | VBAT_P min  MCU            U2 off / U5 off   U2 back  | Q2 Vgs>8 V again  Q2 Tj max       SOA ratio']
    g=lambda v: ('%7.2f ms'%(v*1e3)) if v is not None else '     none'
    for x in R:
        c,c601=x['a']; s=x['soa']
        out.append('%4.1f %-42s %3.0f nF | %6.2f V   %-14s %s / %s %s | %s     %4.0f F (%3.0f C)  %.2f%s'%(c[0],str(c[1:7]),c601*1e9,x['vpmin'],
            'alive' if x['dead'] is None else 'RESET at %.2f ms'%((x['dead']-S.T_SH)*1e3),g(x['u2d']),g(x['u5d']),g(x['u2back']),g(x['vgs_on']),F(x['tj']),x['tj'],s[0],
            '  WARN '+x['warn'] if x['warn'] else ''))
    txt='\n'.join(out); print(txt); open(os.path.join(HERE,'results','s1b_recover_mod.txt'),'w').write(txt+'\n')
