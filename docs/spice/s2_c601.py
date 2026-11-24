#!/usr/bin/env python3
"""Sim 2b: Q2 cold-start SOA vs the effective value of C601 (U1 HGATE dV/dt cap behind R1001 1k).
C601 is an X7R 0603 100 V part; its effective value at 30-45 V bias, -40 F (-40 C) and -10 % tolerance can be 60-70 % of nominal.
Drawn: 22 nF (CC0603KRX7R0BB223). Proposed/applied: 100 nF (CL10B104KC8NNNC, C15725, already on the BOM, same 0603 pad).
Cold start as s2_start.py (U2 79.5 W + U5 2.1 W behind the hold-off, battery 0 -> Vb in 10 us, Rb 15 mOhm / Lb 0.5 uH),
hold-off BJTs at 185 F (85 C). SOA = hand-calc soa_check on the simulated Q2 Vds/Id; Tj = vendor BSC070 thermal network.
Usage: s2_c601.py mod|split"""
import sys, multiprocessing as mp, os
from fe import *
def one(a):
    br,c601,ihg,V=a
    p=dict(V=V,Rb=0.015,Lb=0.5e-6,branch=br,ihg=ihg,c601=c601,u2=dict(ss0=0),u5=dict(),vb_src='Vbat vb 0 PWL(0 0 10u %g)'%V)
    tst=V/(ihg/(c601+1e-9))+16e-3
    r=run(frontend(p),['v(VBAT_P)','v(VBAT_DD,VBAT_PS)','i(VQ2)','v(tj2)','v(xu2.runs)'],tst,2e-6,'s2c_%s_%g_%g_%g'%(br,c601*1e9,ihg*1e6,V),tmax=4e-6,temp=85)
    t=r['t']
    return a,soa(r),first(t,r['v(VBAT_P)']>0.97*V),float(r['v(tj2)'].max()),first(t,r['v(xu2.runs)']>0.5)
if __name__=='__main__':
    br=sys.argv[1]
    J=[(br,nom*f,i,V) for nom in (22e-9,100e-9) for f in ((0.6,0.7,0.85,1.0,1.1)) for i in (39e-6,75e-6) for V in (12.0,24.0,32.0)]
    with mp.Pool(8) as P: R=P.map(one,J,chunksize=1)
    out=[__doc__,'','Branch %s'%br,'C601 nominal  effective  HGATE  Vb   | ramp to 97 %  U2 starts | SOA ratio (tau, Veff, Iavg)       Q2 Tj max']
    for (b,c,i,V),s,tr,tj,tu2 in R:
        nom=22 if c<40e-9 else 100
        out.append('  %3d nF      %5.1f nF   %2.0f uA %4.1f | %6.1f ms    %6s   | %.2f (%.0e s, %4.1f V, %.3f A) %s  %4.0f F (%3.0f C)'%(nom,c*1e9,i*1e6,V,tr*1e3,
            ('%5.1f ms'%(tu2*1e3)) if tu2 else '  >end',s[0],s[1],s[2],s[3],'EXCEEDED' if s[0]>1 else ('<10%% margin' if s[0]>0.9 else 'OK        '),F(tj),tj))
    for nom in (22,100):
        S=[x for x in R if (x[0][1]<40e-9)==(nom==22)]
        out.append('WORST with %d nF nominal (60-110 %% band): %.2f'%(nom,max(x[1][0] for x in S)))
    txt='\n'.join(out); print(txt); open(os.path.join(HERE,'results','s2_c601_%s.txt'%br),'w').write(txt+'\n')
