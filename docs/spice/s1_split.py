#!/usr/bin/env python3
"""Sim 1 (split): dead short at CRANK_OUT (J23), downstream of U45 TPS48100-Q1 and Q47/Q48 BSC070N10NS5.
VENDOR models: TI TPS48100-Q1 (SLUM908, unencrypted, runs in ngspice) and Infineon BSC070N10NS5 with its thermal network.
Netlist (kicad-cli, m7-split-p7): J23 VBAT_ESTOP_IN -> Q70/Q71 SQD40P10-40L (parallel, modelled 20 mOhm) -> VBAT_ESTOP
[D126 SMDJ40CA, C199/C203 100n, U45 VS/CS+, EN/UVLO R298 100k / R299 27k] -> R303 20 mOhm -> CRANK_DRN -> Q47 || Q48 ->
CRANK_OUT [C202 470n BST-SRC, D69 SMDJ40CA, D72 SK1010C to GND] -> J23 -> output harness Ls / Rd2 -> short.
U45: ISCP R300 40.2k, TMR C201 4.7n, G1PU via R301 10R, G1PD via R302 0R, CS_SEL GND, INP1 high.
VBAT_ESTOP is the separate J23 feed (power-box F2 10 A); it does NOT pass through Q2 / BAT_IN, so this event cannot load Q2.
Feed harness Rb 15/35 mOhm x Lb 0.5/2 uH; output harness Ls 0.5/2 uH x Rd2 12/25 mOhm; Vb 12/24/32 V. U45 starts up
(BST charge pump, ~16 ms), the channel is on with a 1 A load, the short closes at 25 ms.
Usage: python3 s1_split.py -> results/s1_short_split_crank.txt"""
import os, sys, itertools, numpy as np, multiprocessing as mp
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from fe import run, F, integ, first, TVS
T_SH=25e-3
def one(a):
    V,Rb,Lb,Ls,Rd2=a
    L=['.include %s/models/TPS48100-Q1_TRANS.lib'%HERE,'.include %s/models/OptiMOS5_100V_Spice.lib'%HERE,'.include %s/models/behav.lib'%HERE,
       '.include %s/models/small.lib'%HERE,
       'Vbat vb 0 PWL(0 0 10u %g)'%V,'Rb vb nb %g'%Rb,'Lb nb ESTIN %g'%Lb,'RQ70 ESTIN VBAT_ESTOP 20m',
       'XD126 VBAT_ESTOP 0 TVSCA PARAMS: vbr=%g rd=%g'%TVS['SMDJ40CA'],'C199 VBAT_ESTOP 0 160n',
       'R303 VBAT_ESTOP CRANK_DRN 20m','Vtc tc 0 65',
       'VQ CRANK_DRN qd 0','XQ47 qd CRANK_G CRANK_OUT tj47 tc BSC070N10NS5 PARAMS: Zthtype=1','XQ48 qd CRANK_G CRANK_OUT tj48 tc BSC070N10NS5 PARAMS: Zthtype=1',
       'R301 G1PU CRANK_G 10','R302 G1PD CRANK_G 1m','C202 BST CRANK_OUT 470n',
       'XD69 CRANK_OUT 0 TVSCA PARAMS: vbr=%g rd=%g'%TVS['SMDJ40CA'],'D72 0 CRANK_OUT DSS310','R352 CRANK_OUT 0 100k',
       'R298 VBAT_ESTOP EN 100k','R299 EN 0 27k','VINP INP1 0 5','RFLT FLT VPU 10k','VPU VPU 0 3.3',
       'R300 ISCP 0 40.2k','C201 TMR 0 4.7n',
       'XU45 BST CRANK_DRN VBAT_ESTOP 0 EN FLT G1PD G1PU G2 0 INP1 0 ISCP 0 CRANK_OUT TMR VBAT_ESTOP TPS48100-Q1_TRANS',
       'RLOAD CRANK_OUT 0 %g'%V,
       'Ls CRANK_OUT ls1 %g'%Ls,'Rd2 ls1 ls2 %g'%Rd2,'Bsh ls2 0 I = V(ls2)*(1e3*max(min(V(shc),1),0)+1e-9)','Vsh shc 0 PWL(0 0 %g 0 %g 1)'%(T_SH,T_SH+1e-9)]
    name='s1sp_%g_%g_%g_%g_%g'%(V,Rb*1e3,Lb*1e6,Ls*1e6,Rd2*1e3)
    r=run(L,['i(VQ)','v(VBAT_ESTOP)','v(CRANK_OUT)','v(qd,CRANK_OUT)','v(tj47)','v(FLT)','v(CRANK_G,CRANK_OUT)','i(Lb)'],T_SH+0.6e-3,0.5e-6,name,tmax=0.5e-6,
          opts='',timeout=3000)
    t=r['t']; m=t>=T_SH-1e-6; iq=r['i(VQ)']
    on=float(np.interp(T_SH-10e-6,t,r['v(CRANK_OUT)']))
    kpk=np.argmax(np.where(m,iq,-1)); toff=first(t[kpk:],iq[kpk:]<1.0)
    vds=r['v(qd,CRANK_OUT)']
    return dict(a=a,v_on=on,ipk=float(iq[m].max()),toff=(toff-T_SH) if toff else None,tpk=float(t[kpk]-T_SH),vE=float(r['v(VBAT_ESTOP)'][m].max()),
                vneg=float(r['v(CRANK_OUT)'][m].min()),tj=float(r['v(tj47)'][m].max()),E=integ(t,np.maximum(vds,0)*np.maximum(iq,0),T_SH-1e-6)/2,
                flt=float(r['v(FLT)'][-1]),i2t=integ(t,r['i(Lb)']**2,T_SH-1e-6),warn=r.get('_warn'))
if __name__=='__main__':
    G=[(V,Rb,Lb,Ls,Rd2) for V in (12.0,24.0,32.0) for (Rb,Lb) in ((0.015,0.5e-6),(0.035,2e-6)) for (Ls,Rd2) in ((0.5e-6,0.012),(2e-6,0.025))]
    with mp.Pool(8) as P: R=P.map(one,G,chunksize=1)
    out=[__doc__,'','Vb   feed Rb/Lb      out Ls/Rd2     | CRANK_OUT before  I peak (t)          off after  | VBAT_ESTOP max  CRANK_OUT min | per-FET E  FET Tj max       FLT end  F2 I2t']
    for x in R:
        V,Rb,Lb,Ls,Rd2=x['a']
        out.append('%4.1f %2.0fm/%3.1fuH     %3.1fuH/%2.0fm     | %5.1f V          %6.1f A (%5.1f us)  %s | %6.1f V         %6.2f V      | %6.1f mJ  %4.0f F (%3.0f C)   %4.1f V  %.4f A2s%s'%(
            V,Rb*1e3,Lb*1e6,Ls*1e6,Rd2*1e3,x['v_on'],x['ipk'],x['tpk']*1e6,('%6.1f us'%(x['toff']*1e6)) if x['toff'] else '  none  ',x['vE'],x['vneg'],x['E']*1e3,F(x['tj']),x['tj'],x['flt'],x['i2t'],
            '  WARN '+x['warn'] if x['warn'] else ''))
    txt='\n'.join(out); print(txt); open(os.path.join(HERE,'results','s1_short_split_crank.txt'),'w').write(txt+'\n')
