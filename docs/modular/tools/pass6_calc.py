#!/usr/bin/env python3
"""Pass 6 deep review (Nov 24, 2026 HST): numbers behind /workspace/review/modular_pass6.md and MOD section 18.
Q2 (U1 HGATE FET) linear-mode stress at cold start with the real boot load and after a supply interruption (warm restart),
channel -> card selectivity with the TPS16630 limit, SS310B hot leakage and OUT clamp. Same Q2 / gate / SOA model as kick_calc.hotplug."""
import sys,os,math
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kick_calc as k
F=lambda c:c*9/5+32
print(__doc__)

def boot(Vb,ihg,c_dvdt=22e-9,vp0=0.0,p_u2=0.0,u2_on_at_start=False,iin_max=3.56,p_u5=0.0,cgd=200e-12,K=30.0,Vt=2.86,Rfe=0.008,
         t_ss=7.5e-3,eta=0.88,v_u2=3.8,v_u5=4.2,T=120e-3,dt=5e-8):
    """VBAT_P ramp through Q2 (follower on HGATE) from vp0. The HGATE node starts at vp0: while U1 holds HGATE off, the pin is tied to OUT,
    so C601 is parked at VBAT_P (SNOSD95C 9.3.2.2). Loads: U2 LM5176 (p_u2 W out, soft start t_ss, input current <= iin_max, RAIL_PLAN) once
    VBAT_P > v_u2 if its EN/UVLO is already high (C602 still charged); U5 LMR36506 (EN = VIN) constant p_u5 W in above v_u5: at boot the
    TPS2116 runs the whole +3V3_SAFE load from +3V3_BK until +3V3 is up."""
    Cc=4*10e-6*0.65+2.2e-6*0.6+0.2e-6+2*100e-6
    vp=vp0; vg=vp0; t=0.0; t_on=None; trv=[]; tri=[]; av=ai=0.0; na=0; s10=int(round(1e-5/dt)); E=0.0
    while t<T:
        iD=K*max(vg-vp-Vt,0)**2; vds=Vb-vp; iD=min(iD,max(vds,0)/Rfe)
        if u2_on_at_start and t_on is None and vp>=v_u2: t_on=t
        ild=0.0
        if t_on is not None: ild=min(p_u2*min(1.0,(t-t_on)/t_ss)/eta/max(vp,1.0),iin_max)
        if vp>v_u5: ild+=p_u5/vp
        dvp=(iD-ild)/Cc*dt
        vg=min(vg+(ihg*dt+2.1e-9*dvp)/(2.1e-9+cgd+c_dvdt),vp+dvp+11.1); vp=max(vp+dvp,0.0)
        E+=iD*max(vds,0)*dt; av+=max(vds,0); ai+=iD; na+=1
        if na>=s10: trv.append(av/na); tri.append(ai/na); av=ai=0.0; na=0
        t+=dt
        if vp>Vb-0.3 and t>1e-3 and (t_on is None or t>t_on+t_ss) and iD<ild+0.3: break
    return E,t,k.soa_check(np.array(trv),np.array(tri))

print('== 1. Cold start at 32 V (C601 22 nF + 1k, C602 holds U2 off until after the ramp): U5 is NOT off')
print('U5 LMR36506 has EN tied to VIN (VBAT_P): it starts at ~4.2 V and, through the TPS2116, carries all of +3V3_SAFE (<= 0.55 A bound,')
print('RAIL_PLAN) while Q2 is still in its 10-20 ms linear ramp. Input power 0.5 / 1.0 / 2.1 W = boot-typical / mid / 0.55 A bound at eta 0.85.')
for ihg in (39e-6,75e-6):
    for p in (0.0,0.5,1.0,2.1):
        E,t,sc=boot(32.0,ihg,p_u5=p)
        print('  HGATE %2.0f uA, U5 %.1f W: Q2 E %4.0f mJ, ramp %4.1f ms, SOA ratio %.2f (%s)'%(ihg*1e6,p,E*1e3,t*1e3,sc[0],'OK' if sc[0]<=1 else 'EXCEEDED'))

print('\n== 2. Warm restart after a supply interruption (loose battery terminal, isolator blip, U1 UVLO/OV): C602 does not re-arm')
print('U1 EN/UVLO has no filter: BAT_IN < ~5.2 V turns HGATE off in 3-6 us. VBAT_P (230 uF) then feeds U2 at up to 70 W: it falls ~10 V/ms')
print('at 32 V and U2 stops near its 3.5-4 V floor within ~1-2 ms. C602 keeps U2 EN/UVLO above 1.23 V for:')
for Vb in (13.8,24.0,28.8,32.0):
    en0=Vb*33/133
    print('  %4.1f V: EN starts at %.2f V -> held for %3.0f-%3.0f ms (tau 124-273 ms)'%(Vb,en0,124*math.log(en0/1.23),273*math.log(en0/1.23)))
print('so any interruption from ~1 ms up to that hold time restarts U2 the moment VBAT_P passes its floor, while Q2 is still ramping.')
print('Q2 ramp from VBAT_P = 4 V (U2 stopped) or Vb/2 (short dip), U2 70 W out, input <= 3.56 A, U5 1 W:')
for Vb in (32.0,28.8,24.0,13.8):
    for vp0 in (4.0,Vb/2):
        for ihg in (39e-6,75e-6):
            E,t,sc=boot(Vb,ihg,vp0=vp0,p_u2=70.0,u2_on_at_start=True,p_u5=1.0)
            print('  Vb %4.1f V from %4.1f V, HGATE %2.0f uA: Q2 E %5.0f mJ, ramp %5.1f ms, SOA ratio %5.2f (%s)'%(Vb,vp0,ihg*1e6,E*1e3,t*1e3,sc[0],'OK' if sc[0]<=1 else 'EXCEEDED'))
print('Same restart (from 4 V) with other C601 values: the FET, not the capacitor, is the root cause')
for Vb in (32.0,24.0):
    for cd in (0.0,4.7e-9,22e-9):
        for ihg in (39e-6,75e-6):
            E,t,sc=boot(Vb,ihg,c_dvdt=cd,vp0=4.0,p_u2=70.0,u2_on_at_start=True,p_u5=1.0,dt=5e-9 if cd==0 else 2e-8)
            print('  Vb %4.1f V, C601 %4.1f nF, HGATE %2.0f uA: Q2 E %5.0f mJ, SOA ratio %5.2f'%(Vb,cd*1e9,ihg*1e6,E*1e3,sc[0]))
print('BSC070N10NS5 (OptiMOS 5, Diagram 3) linear-mode capability from the kick_calc digitisation, Tc 77 F (25 C):')
for V in (10,20,30):
    print('  %2d V: 1 ms %5.2f A, 10 ms %5.2f A'%(V,k.soa_i(V,1e-3),k.soa_i(V,1e-2)))
print('  For comparison, the Nexperia PSMN4R8-100YSE hot-swap ASFET (LFPAK56E) is rated 8 A at 50 V for 10 ms and 18 A at 50 V for 1 ms')
print('  (Nexperia datasheet / ASFET note, Nov 24, 2026). JLC stock today: 0 (C5122725).')

print('\n== 3. Channel -> card selectivity with the slot eFuse limit (HSO-5 / BRK-4 channel limit TPS1HTC30 33.2k: 2.41-3.61 A)')
print('A shorted channel draws up to 3.61 A; the rest of that card keeps its preload. If preload + 3.61 A > I_OL(min), the eFuse goes into')
print('current limit, FLT# falls after 1.09-1.6 ms and FW C5.1 cuts the whole card (Pass 4: the slot switch tripped at 10.6-16.5 A, so it did not).')
tauH=0.316*0.99*0.9*0.9*(1-0.013); tauR=0.195*0.99*0.9*0.9*(1-0.013)
def ttrip(I,I0,Ith,ta): return ta*math.log((I-I0)/(I-Ith)) if I>Ith else float('inf')
for lab,R,lo,hi in (('as built 4.02k',4.02,4.185*4.02/(4.02*1.01),4.815*4.02/(4.02*0.99)),('option 3.09k (UL 2367 needs >= 3k)',3.09,5.58*3.0/(3.09*1.01),6.42*3.0/(3.09*0.99))):
    print('  %-36s I_OL %.2f-%.2f A -> same-card preload allowed with one channel shorted: %.2f A'%(lab,lo,hi,lo-3.61))
    for m,I0,Ith,tau in (('HOT',2.4,3.15,tauH),('ROOM',4.0,5.11,tauR)):
        tt=ttrip(I0+hi,I0,Ith,tau)
        print('      %-4s bank overload trip with one card at I_OL max on top of the budget: >= %.1f ms (FW 20 ms card-cut margin %.1f ms)'%(m,tt*1e3,tt*1e3-20))
    print('      eFuse in limit at 32 V, Vout ~ 18 V: (32-18) x %.2f A = %.0f W -> TSD in tens of ms, before t_CL 129 ms'%(hi,(32-18)*hi))

print('\n== 4. SS310B (MDD, C14281) reverse leakage hot (closes the Pass 5 open item)')
print('Datasheet (docs/split_evidence/modular_pass6/ss310b_mdd.pdf): IR max 0.3 mA at 77 F (25 C) and 3 mA at 212 F (100 C), at the rated 100 V;')
print('Fig. 2 typical at 32 % of VRRM and 100 C ~0.7 mA. RthJA 60 C/W. Bound used: the 100 V maximum, doubling every 10 C (Schottky rule).')
for Tj in (65,85,100,115,125):
    I=3e-3*2**((Tj-100)/10.0); P=32.0*I; S=P*math.log(2)/10*60
    print('  Tj %3d C (%3.0f F): IR <= %5.2f mA, P <= %4.0f mW at 32 V, dTj %4.1f K, runaway factor %.2f (%s)'%(Tj,F(Tj),I*1e3,P*1e3,P*60,S,'stable' if S<1 else 'UNSTABLE'))
print('-> stable with 2.5x margin at a 212 F (100 C) diode junction; runaway needs the junction above ~234 F (112 C). Place it away from the eFuse')
print('   pad heat (layout note); the slot leakage (<= 3 mA) is negligible for VBAT_SLOTS.')

print('\n== 5. SS310B clamp level on the faulted slot (model: Vf0 1.2 V + 20 mOhm, MDD Fig. 3 ~1.15 V @ 10 A, ~1.35 V @ 20 A)')
for I in (20,60,100,300):
    print('  loop current %3d A at turn-off: OUT ~ -%.1f V for ~%.1f us (Ls 50 nH)'%(I,1.2+0.02*I,50e-9*I/(1.2+0.02*I+I*0.012)*1e6))
print('  (realistic kick_calc corners, FET saturating ~60 A: -2.2 V; pessimistic unsaturated 300+ A corners: -5.9 to -7.5 V, linear r_dyn extrapolated')
print('   beyond Fig. 3, so an upper bound. SS310B pulse stress: (300 A)^2 x 1 us = 0.09 A2s vs IFSM 80 A half-sine 8.3 ms ~ 27 A2s: OK.)')
print('  TPS16630 OUT abs max is -0.3 V (static). TI 9.4.1 accepts the inductive negative spike with a Schottky at OUT/GND. Bench test 17.9 #2')
print('  now records the OUT minimum and checks the eFuse after 50 shorts instead of a -1.5 V pass line.')
