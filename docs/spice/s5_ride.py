#!/usr/bin/env python3
"""Sim 5 (and the warm-restart half of sim 2): battery interruption while running, then the battery returns.
Running state at t = 0: U2 at full load (79.5 W in), U5 2.1 W bound (worst case: the TPS2116 moves +3V3_SAFE onto +3V3_BK as soon
as U2's chain drops; the real MCU-domain load is lower). Two interruption types:
  O = battery side opens (loose terminal / connector): BAT_IN floats on C297 + its own loads.
  G = battery side opens and BAT_IN is pulled to 0 V through 1 Ohm (shared feed collapsing, e.g. a hard short upstream).
Interruption lengths 0.1-20 ms, then the battery returns through Rb 15 mOhm / Lb 0.5 uH.
MCU alive = U2 running (its +3V3 chain) or U5 running (+3V3_BK). Conservative: the +12 V / +3V3 output caps' own hold-up after U2
stops is not counted. Q2 SOA on the return = hand-calc soa_check on 10 us bins; Tj from the vendor thermal network.
Options (recommend only; NOT in the schematics):
  asis = drawn circuit (D402 pin 2 lets the hold-off pull U5_EN).
  A    = hold-off may stop U5 only while +3V3_BK is down: D402 pin 2 not fitted; Q123 MMBT3904 (C = U5_EN) driven from the Q121
         collector through 47k (100k B-E); Q124 MMBT3904 (C = Q123 base) driven from +3V3_BK through 47k. +2 BJT, +3 R.
  B    = A + U5 hold-up: U5 VIN fed from VBAT_P through D_A SS110; C_HU 2x 100 uF 63 V (EEETG1J101UP, already on the BOM)
         charged through R_HU 2.2k with D_B SS110 across it for discharge into U5 VIN; U5 EN divider from U5 VIN.
         R_HU keeps the C_HU charge off Q2 during the ramp. +2 SS110, +2 caps, +1 R on top of A.
Usage: s5_ride.py mod|split"""
import sys, multiprocessing as mp, numpy as np, os
from fe import *
T0=0.5e-3
def ride_lines(opt):
    if opt=='asis': return {},[]
    A=['B3V3 v3bk 0 V = 3.3*V(U5_ALIVE)','RQA ho_c q123b 47k','RQAB q123b 0 100k','Q123 U5_EN q123b 0 Q2N3904',
       'RQB v3bk q124b 47k','Q124 q123b q124b 0 Q2N3904']
    if opt=='A': return dict(u5_holdoff=False),A
    B=A+['DA VBAT_P U5VIN DSS110','RHU U5VIN chu 2.2k','DB chu U5VIN DSS110','CHU chu1 0 160u','RCHU chu chu1 0.4','CU5 U5VIN 0 10u']
    if opt=='B': return dict(u5_holdoff=False,u5en_src='U5VIN',u5vin='U5VIN'),B
def one(a):
    br,V,typ,tint,opt,ihg=a
    po,extra=ride_lines(opt)
    p=dict(V=V,Rb=0.015,Lb=0.5e-6,branch=br,ihg=ihg,u2=dict(ss0=1),u5=dict(vin=po.get('u5vin','VBAT_P')),bat_switch=True,
           bat_short=(typ=='G'),r_short=1.0,extra=extra+['Vbsw bsw 0 PWL(0 1 %g 1 %g 0 %g 0 %g 1)'%(T0,T0+1e-7,T0+tint,T0+tint+1e-7)]
           +(['Vbsh bsh 0 PWL(0 0 %g 0 %g 1 %g 1 %g 0)'%(T0,T0+1e-7,T0+tint,T0+tint+1e-7)] if typ=='G' else []))
    p.update({k:v for k,v in po.items() if k in ('u5_holdoff','u5en_src')})
    ns=ns_on(V); 
    if opt=='B': ns.update(U5VIN=V-0.3,chu=V-0.3,chu1=V-0.3)
    tst=T0+tint+1.1*V/(ihg/(C601_DEFAULT+1e-9))+14e-3   # covers the slowest HGATE re-ramp
    name='s5_%s_%g_%s_%g_%s_%g'%(br,V,typ,tint*1e3,opt,ihg*1e6)
    r=run(frontend(p),['v(BAT_IN)','v(VBAT_P)','v(VBAT_DD,VBAT_PS)','i(VQ2)','v(tj2)','v(xu2.runs)','v(U5_ALIVE)','v(HO_F)'],tst,2e-6,name,tmax=5e-6,nodeset=ns)
    t=r['t']; alive=(r['v(U5_ALIVE)']>0.5)|(r['v(xu2.runs)']>0.5)
    m=t>T0; dead=first(t[m],~alive[m])
    u5d=first(t[m],r['v(U5_ALIVE)'][m]<0.5); u2d=first(t[m],r['v(xu2.runs)'][m]<0.5)
    s=soa(r,t0=T0+tint)
    return dict(a=a,survive=dead is None,tdead=(dead-T0) if dead else None,u5d=(u5d-T0) if u5d else None,u2d=(u2d-T0) if u2d else None,
                soa=s,tj=float(r['v(tj2)'].max()),E=integ(t,np.maximum(r['v(VBAT_DD,VBAT_PS)'],0)*np.maximum(r['i(VQ2)'],0),T0+tint),
                vp_ret=float(np.interp(T0+tint,t,r['v(VBAT_P)'])),iq2=float(r['i(VQ2)'][t>T0+tint].max()),warn=r.get('_warn'))
if __name__=='__main__':
    br=sys.argv[1]; opts=sys.argv[2].split(',') if len(sys.argv)>2 else ['asis','A','B']
    TI=[0.1e-3,0.2e-3,0.5e-3,1e-3,2e-3,5e-3,10e-3,20e-3]
    jobs=[(br,V,typ,ti,opt,ihg) for opt in opts for V in (12.0,24.0,32.0) for typ in ('O','G') for ti in TI for ihg in (39e-6,75e-6)]
    with mp.Pool(8) as P: R=P.map(one,jobs,chunksize=1)
    import pickle; pickle.dump(R,open(os.path.join(HERE,'work','s5_%s_%s.pkl'%(br,'_'.join(opts))),'wb'))
    out=[__doc__,'','Branch %s.'%br,'opt  Vb   type  t_int ms  HGATE | VBAT_P at return  MCU   (U2 off / U5 off after the break starts, ms) | Q2 Ipk  Q2 E mJ  Tj max         SOA ratio']
    f=lambda v: '%6.2f'%(v*1e3) if v is not None else '     -'
    for x in R:
        _,V,typ,ti,opt,ihg=x['a']; s=x['soa']
        out.append('%-4s %4.1f  %s   %6.1f    %2.0f uA | %6.1f V          %-5s (%s / %s)  | %5.0fA %6.1f  %4.0f F (%3.0f C)  %.2f%s'%(opt,V,typ,ti*1e3,ihg*1e6,x['vp_ret'],
            'alive' if x['survive'] else 'RESET',f(x['u2d']),f(x['u5d']),x['iq2'],x['E']*1e3,F(x['tj']),x['tj'],s[0],'  WARN '+x['warn'] if x['warn'] else ''))
    out.append('\nSummary: longest interruption with the MCU alive (all HGATE corners), and worst Q2 SOA over all lengths')
    for opt in opts:
        for V in (12.0,24.0,32.0):
            for typ in ('O','G'):
                S=[x for x in R if x['a'][4]==opt and x['a'][1]==V and x['a'][2]==typ]
                ok=[ti for ti in TI if all(x['survive'] for x in S if x['a'][3]==ti)]
                # longest contiguous survived length from the shortest
                lc=0
                for ti in TI:
                    if ti in ok: lc=ti
                    else: break
                out.append('  %-4s %4.1f V type %s: MCU survives up to %s ms (first reset at %s ms); worst SOA %.2f'%(opt,V,typ,
                    ('%g'%(lc*1e3)) if lc else '<0.1',('%g'%(min([ti for ti in TI if ti not in ok])*1e3)) if len(ok)<len(TI) else '>20',max(x['soa'][0] for x in S)))
    txt='\n'.join(out); print(txt); open(os.path.join(HERE,'results','s5_ride_%s_%s.txt'%(br,'_'.join(opts))),'w').write(txt+'\n')
