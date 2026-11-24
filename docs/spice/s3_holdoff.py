#!/usr/bin/env python3
"""Sim 3: the 11-part Q2 hold-off (D401, Q121 MMBT5401, R1121 22k, R1122 68k, R1123 22k, C1121 100n, R1124 100k, Q122 MMBT3904,
D402 BAT54C) with the U2 EN/UVLO (R4 100k / R5 33k / C602 1u) and U5 EN (R1125 100k / R1126 47k) networks, transistor level.
(a) DC threshold: BAT_IN - VBAT_P at which U2 EN/UVLO (BB_UVLO) is pulled below 1.17 V and U5_EN below 1.16 V, at VBAT_P 12 / 24 V,
    -40 / 77 / 185 F (ngspice .temp; vendor-equivalent ON Semi 2N5401/2N3904/1N4148 models, BAT54 fitted).
(b) Engage timing: VBAT_P held at Vb - dV, BAT_IN steps up by dV; time to Q122 on (collector current > 1 mA), BB_UVLO < 1.17 V, U5_EN < 1.16 V.
(c) U5 EN turn-on point with the hold-off idle (BAT_IN = VBAT_P + 0.1 V): VBAT_P at U5_EN = 1.16 / 1.26 / 1.36 V.
Usage: s3_holdoff.py [mod|split] -> results/s3_holdoff.txt (the circuit is identical on both branches)."""
import sys, numpy as np, subprocess, os
from fe import HERE, run, F, first
NET='''.include %s/models/small.lib
VBP VBAT_P 0 DC {vp}
VBI BAT_IN 0 {vbi}
D401 BAT_IN ho_a D1N4148
Q121 ho_c ho_b ho_a Q2N5401
R1121 ho_a ho_b 22k
R1122 ho_b VBAT_P 68k
R1123 ho_c HO_F 22k
C1121 HO_F 0 100n
R1124 HO_F 0 100k
VQK HO_K hk 0
Q122 hk HO_F 0 Q2N3904
D402A BB_UVLO HO_K DBAT54
D402B U5_EN HO_K DBAT54
R4 VBAT_P BB_UVLO 100k
R5 BB_UVLO 0 33k
C602 BB_UVLO 0 {c602}
R1125 VBAT_P U5_EN 100k
R1126 U5_EN 0 47k
'''%HERE
def dc_sweep(vp,temp):
    cir=os.path.join(HERE,'work','s3dc_%g_%g.cir'%(vp,temp))
    n=NET.replace('{vp}','%g'%vp).replace('{vbi}','DC %g'%vp).replace('{c602}','1u')
    n+='.temp %g\n.control\ndc VBI %g %g 0.002\nwrdata %s.dat v(BB_UVLO) v(U5_EN) v(HO_F) i(VBI)\n.endc\n.end\n'%(temp,vp,vp+6,cir)
    open(cir,'w').write('* s3 dc\n'+n); subprocess.run(['ngspice','-b',cir],capture_output=True,cwd=HERE)
    d=np.loadtxt(cir+'.dat'); x=d[:,0]-vp
    bb=d[:,1]; u5=d[:,3]
    return first(x,bb<1.17),first(x,u5<1.16)
def tran(vb,dv,temp,c602=1e-6):
    vp=vb-dv
    n=NET.replace('{vp}','%g'%vp).replace('{vbi}','PWL(0 %g 1u %g 2u %g)'%(vp,vp,vb)).replace('{c602}','%g'%c602)
    r=run(n.splitlines(),['i(VQK)','v(BB_UVLO)','v(U5_EN)','v(HO_F)'],2e-3,0.5e-6,'s3tr_%g_%g_%g'%(vb,dv,temp),temp=temp,tmax=2e-6)
    t=r['t']-2e-6
    bb0=r['v(BB_UVLO)'][0]>1.17; u0=r['v(U5_EN)'][0]>1.16
    return first(t,r['i(VQK)']>1e-3),(first(t,r['v(BB_UVLO)']<1.17) if bb0 else None),(first(t,r['v(U5_EN)']<1.16) if u0 else None)
def u5on(temp):
    cir=os.path.join(HERE,'work','s3u5_%g.cir'%temp)
    n=NET.replace('{vp}','0').replace('{vbi}','DC 0.1').replace('{c602}','1u')
    n=n.replace('VBI BAT_IN 0 DC 0.1','VBI BAT_IN VBAT_P DC 0.1').replace('VBP VBAT_P 0 DC 0','VBP VBAT_P 0 DC 0')
    n+='.temp %g\n.control\ndc VBP 0 8 0.001\nwrdata %s.dat v(U5_EN)\n.endc\n.end\n'%(temp,cir)
    open(cir,'w').write('* s3 u5\n'+n); subprocess.run(['ngspice','-b',cir],capture_output=True,cwd=HERE)
    d=np.loadtxt(cir+'.dat'); return [first(d[:,0],d[:,1]>=th) for th in (1.16,1.26,1.36)]
if __name__=='__main__':
    os.makedirs(os.path.join(HERE,'work'),exist_ok=True)
    T=[(-40,'cold'),(25,'room'),(85,'hot')]
    out=[__doc__,'','(a) DC threshold BAT_IN - VBAT_P (V). Hand calc (pass6_fix_calc / MOD 19.1): 3.79 cold / 3.09 room / 2.47 hot.',
         '   temp              VBAT_P   U2 off (BB_UVLO<1.17)   U5 off (U5_EN<1.16)']
    for vp in (12.0,24.0):
        for tc,lab in T:
            a,b=dc_sweep(vp,tc)
            out.append('   %4.0f F (%3d C) %-4s %5.1f V        %5.2f V                %5.2f V'%(F(tc),tc,lab,vp,a,b))
    out+=['','(b) Engage timing after BAT_IN steps dV above VBAT_P (ms). Hand calc engage (HO_F -> Q122 on): 46-58 us at 32 V, 63-78 us at 24 V,',
          '    113-142 us at 13.8 V, 209-268 us at 8 V (room/cold, full step); up to ~0.53 ms just above threshold (4 V step, cold); U2 off <= 0.25 ms after engage.',
          '   Vb     dV    temp            Q122 on    U2 EN<1.17 V   U5 EN<1.16 V']
    import multiprocessing as mp
    jobs=[(vb,dv,tc) for vb in (8.0,13.8,24.0,32.0) for dv in sorted(set((4.0,6.0,vb-4.0))) for tc,_ in T if dv<=vb-4.0]
    with mp.Pool(8) as P: R=P.starmap(tran,jobs)
    fm=lambda x: '%7.3f'%(x*1e3) if x is not None else '    n/a'
    for (vb,dv,tc),(a,b,c) in zip(jobs,R):
        out.append('   %4.1f  %4.1f  %4.0f F (%3d C)  %s     %s        %s'%(vb,dv,F(tc),tc,fm(a),fm(b),fm(c)))
    out+=['   (dV = Vb - 4 V: warm restart from VBAT_P 4 V. n/a = that EN pin was already below its threshold before the step, or Q122 had nothing to sink.)','',
          '(c) U5 turn-on with the hold-off idle: VBAT_P where U5_EN reaches 1.16 / 1.26 / 1.36 V (EN min / typ / max). Hand calc 3.63-4.25 V.']
    for tc,lab in T:
        a,b,c=u5on(tc); out.append('   %4.0f F (%3d C): %.2f / %.2f / %.2f V'%(F(tc),tc,a,b,c))
    txt='\n'.join(out); print(txt); open(os.path.join(HERE,'results','s3_holdoff.txt'),'w').write(txt+'\n')
