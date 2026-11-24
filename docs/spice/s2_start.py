#!/usr/bin/env python3
"""Sim 2: cold start (battery connected with everything discharged) into the full load and bulk caps.
Deck: fe.frontend (vendor BSC070N10NS5 Q1/Q2 with thermal network, behavioral LM74800 HGATE 39/75 uA into R1001 1k + C601 22n,
transistor-level hold-off), U2 LM5176 as a 79.5 W input load with 7.5 ms soft start gated by BB_UVLO (C602 1 uF or 0.5 uF derated),
U5 LMR36506 as a 2.1 W load gated by U5_EN. Battery 0 -> Vb in 10 us through the harness (Rb 15 mOhm, Lb 0.5 uH, as the hand calc).
Q2 SOA = the hand calc's soa_check (BSC070 Diagram 3 derated to Tc 149 F / 65 C) on 10 us bins of the simulated Vds/Id;
Q2 Tj = the vendor model's own thermal network (Zthtype 1 = max) from Tcase 149 F (65 C).
Hand calc: modular pass6_fix_calc.txt section 2 (worst 0.89 at 32 V), split p7_calc.txt section 3 (worst 0.91 at 32 V, inrush ~0.6 A).
Usage: s2_start.py mod|split"""
import sys, itertools, multiprocessing as mp, numpy as np, os
from fe import *
def one(a):
    br,V,ihg,temp,c602,cold=a
    p=dict(V=V,Rb=0.015,Lb=0.5e-6,cold=cold,branch=br,ihg=ihg,c602=c602,u2=dict(ss0=0),u5=dict(),
           vb_src='Vbat vb 0 PWL(0 0 10u %g)'%V)
    tst=V/(ihg/23e-9)+14e-3
    name='s2_%s_%g_%g_%g_%g_%d'%(br,V,ihg*1e6,temp,c602*1e6,cold)
    r=run(frontend(p),['v(BAT_IN)','v(VBAT_P)','v(VBAT_DD,VBAT_PS)','i(VQ2)','v(tj2)','i(Lb)','v(xu2.runs)','v(U5_ALIVE)','v(HO_F)'],tst,1e-6,name,tmax=2e-6,temp=temp)
    t=r['t']; vp=r['v(VBAT_P)']
    s=soa(r)
    tr=first(t,vp>0.97*V); u2=first(t,r['v(xu2.runs)']>0.5); u5=first(t,r['v(U5_ALIVE)']>0.5)
    # inrush: harness current excluding the first 50 us (cap charge of BAT_IN/VBAT_DD at hot-plug)
    m=t>50e-6
    return dict(a=a,soa=s,tj=float(r['v(tj2)'].max()),E=integ(t,np.maximum(r['v(VBAT_DD,VBAT_PS)'],0)*np.maximum(r['i(VQ2)'],0)),
                ipk=float(r['i(Lb)'][m].max()),iq_ramp=float(np.median(r['i(VQ2)'][(vp>0.2*V)&(vp<0.8*V)])) if ((vp>0.2*V)&(vp<0.8*V)).any() else None,
                tramp=tr,tu2=u2,tu5=u5,iq2pk=float(r['i(VQ2)'][m].max()),warn=r.get('_warn'))
if __name__=='__main__':
    br=sys.argv[1]
    jobs=[(br,V,ihg,temp,c602,cold) for V in (12.0,24.0,32.0) for ihg in (39e-6,75e-6) for temp in (-40,85) for c602 in (1e-6,0.5e-6) for cold in (0,)]
    with mp.Pool(8) as P: R=P.map(one,jobs,chunksize=1)
    import pickle; pickle.dump(R,open(os.path.join(HERE,'work','s2_%s.pkl'%br),'wb'))
    out=[__doc__,'','Branch %s. temp = hold-off BJT/diode temperature (.temp); Tcase 149 F (65 C) for Q2 in every row.'%br,
         'Vb    HGATE  temp   C602 | ramp ms  U5 on ms  U2 on ms | inrush pk (after 50 us)  Q2 I in ramp | Q2 E mJ  Q2 Tj max       SOA ratio (tau, Veff, Iavg)']
    for x in R:
        _,V,ihg,temp,c602,cold=x['a']; s=x['soa']
        f=lambda v: '%6.2f'%(v*1e3) if v is not None else '  none'
        out.append('%4.1f  %2.0f uA  %4.0f F %3.1f uF | %s   %s   %s  | %6.2f A               %5.2f A      | %6.1f  %4.0f F (%3.0f C)   %.2f (%.0e s, %.1f V, %.2f A)%s'%(
            V,ihg*1e6,F(temp),c602*1e6,f(x['tramp']),f(x['tu5']),f(x['tu2']),x['ipk'],x['iq_ramp'] or 0,x['E']*1e3,F(x['tj']),x['tj'],s[0],s[1],s[2],s[3],
            '  WARN '+x['warn'] if x['warn'] else ''))
    w=max(R,key=lambda x:x['soa'][0]); out.append('\nWORST SOA ratio: %.2f at %s'%(w['soa'][0],str(w['a'][1:])))
    txt='\n'.join(out); print(txt); open(os.path.join(HERE,'results','s2_start_%s.txt'%br),'w').write(txt+'\n')
