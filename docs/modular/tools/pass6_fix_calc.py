#!/usr/bin/env python3
"""Pass 6 fixes (Ethan's picks, Nov 24, 2026 HST): B1 Q2 hold-off, M2 R_ILIM 3.09k, M3 engine-slot feeds. Numbers behind MOD section 19.
Same Q2 / HGATE / SOA model as pass6_calc.boot and kick_calc (BSC070N10NS5 SOA, Tc 149 F / 65 C derating), plus the hold-off:
BAT_IN -> D401 1N4148W -> Q121 MMBT5401 E (R1121 22k E-B, R1122 68k B -> VBAT_P); C -> R1123 22k -> HO_F (C1121 100 nF || R1124 100k)
-> Q122 MMBT3904 -> D402 BAT54C -> BB_UVLO (C602, U2 EN/UVLO) and U5_EN (R1125 100k / R1126 47k from VBAT_P).
C602 is 1 uF X7R (0.5-1.1 uF effective; was 10 uF): see section 3 for why."""
import sys,os,math
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kick_calc as k
F=lambda c:c*9/5+32
print(__doc__)

# ---- Pass 8 value check: the drawn parts must be the ones this model assumes (Pass 8 found R1121/R1123 = 2.2k and R1126 = 4.7k:
# mainboard.py's R22K/R47K constants are really the 2.2k/4.7k I2C pull-up parts). Fails the gate if any part drifts.
import re,glob
_ROOT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..'))
_S=''.join(open(f).read() for f in glob.glob(os.path.join(_ROOT,'*.kicad_sch')))
# C601: 100 nF C15725 since the SPICE pass (docs/spice/README.md); the hand-calc model below keeps the Pass 6 22 nF record.
WANT={'R1001':('1k','C21190'),'C601':(None,'C15725'),'C602':(None,'C28323'),'D401':('1N4148W','C81598'),'Q121':('MMBT5401','C8326'),
      'R1121':('22k','C31850'),'R1122':('68k','C23231'),'R1123':('22k','C31850'),'R1124':('100k','C25803'),'C1121':('100n','C14663'),
      'Q122':('MMBT3904','C20526'),'D402':('BAT54C','C37704'),'R1125':('100k','C25803'),'R1126':('47k','C25819')}
print('== 0. Pass 8 value check (drawn hold-off / front-end parts vs this model)')
_bad=0
for ref,(val,lc) in WANT.items():
    m=re.search(r'\(property "Reference" "%s"'%ref,_S); blk=_S[m.start():m.start()+3000] if m else ''
    v=re.search(r'\(property "Value" "([^"]*)"',blk); l=re.search(r'\(property "LCSC" "([^"]*)"',blk)
    v=v.group(1) if v else None; l=l.group(1) if l else None
    ok=m is not None and (val is None or v==val) and l==lc; _bad+=not ok
    print('  %-6s %-10s %-8s %s'%(ref,v,l,'OK' if ok else 'WRONG (want %s %s)'%(val,lc)))
if _bad: sys.exit('Pass 8 value check: %d part(s) differ from the model'%_bad)

# hold-off corners: (label, D401 Vf, Q121 Veb, Q121 beta, Q122 beta, Vbe Q122)
HOT=('hot 185 F (85 C)',0.42,0.50,60.0,40.0,0.55); NOM=('room 77 F (25 C)',0.55,0.62,100.0,60.0,0.65); COLD=('cold -40 F (-40 C)',0.72,0.75,50.0,30.0,0.80)
def vth(c): return c[1]+c[2]*(68+22)/22.0
def pnp_ic(vds,vb,c,vf_node):
    """Q121 collector current for BAT_IN - VBAT_P = vds (BAT_IN = vb), HO_F at vf_node."""
    ve=vds-c[1]                                  # emitter over VBAT_P
    ib=(ve-c[2])/68e3-c[2]/22e3                  # base current = 68k current - 22k E-B current
    if ib<=0: return 0.0
    icsat=max(vb-c[1]-0.2-vf_node,0)/22e3
    return min(c[3]*ib,icsat)

def run(Vb,ihg,c,vp0=0.0,warm=False,u2_full=False,p_u2=70.0,p_u5=2.1,iin_max=3.56,holdoff=True,c602=1.1e-6,en_on=1.17,en_off=1.17,
        u5_on=1.16,c_dvdt=22e-9,cgd=200e-12,K=30.0,Vt=2.86,Rfe=0.008,t_ss=7.5e-3,eta=0.88,v_u2=3.8,T=0.4,dt=1e-7):
    """Returns dict: Q2 energy, ramp time, SOA ratio, hold-off engage time, U2 off time, U2 re-enable time."""
    Cc=4*10e-6*0.65+2.2e-6*0.6+0.2e-6+2*100e-6
    vp=vp0; vg=vp0; t=0.0
    vbb=Vb*33/133 if warm else 0.0               # C602 charged (warm) or empty (cold)
    u2=u2_full and vp0>v_u2; t_on=-1.0 if u2 else None
    vho=0.0; eng=False; t_eng=None; t_u2off=None; t_u2on=None
    trv=[];tri=[]; av=ai=0.0; na=0; s10=int(round(1e-5/dt)); E=0.0
    while t<T:
        vds=Vb-vp
        iD=K*max(vg-vp-Vt,0)**2; iD=min(iD,max(vds,0)/Rfe)
        # hold-off chain
        if holdoff:
            ic=pnp_ic(vds,Vb,c,vho)
            ib2=0.0; inet=ic-vho/100e3
            if vho>=c[5] and inet>0: ib2=inet; vho=c[5]            # Q122 base clamps HO_F at Vbe; surplus is base drive
            else: vho=max(vho+inet/100e-9*dt,0.0)
            isink=c[4]*ib2
            eng=isink>2e-3
            if eng and t_eng is None: t_eng=t
        else: isink=0.0; eng=False
        # BB_UVLO / C602: R4 100k / R5 33k from VBAT_P (Thevenin vp*33/133, 24.8k) minus the hold-off sink (through BAT54C, down to ~0.45 V)
        i_bb=(vp*33/133-vbb)/24.8e3
        if eng and vbb>0.45: i_bb-=isink
        vbb=max(vbb+i_bb/c602*dt,0.0)
        # U2 state
        if u2 and (vbb<en_off or vp<v_u2-0.3):
            u2=False; t_on=None
            if t_u2off is None: t_u2off=t
        elif not u2 and vbb>en_on and vp>=v_u2:
            u2=True; t_on=t
            if t>0 and t_u2on is None: t_u2on=t
        ild=0.0
        if u2: ild=min(p_u2*(1.0 if t_on<0 else min(1.0,(t-t_on)/t_ss))/eta/max(vp,1.0),iin_max)
        # U5: EN = vp*47/147 unless pulled to ~0.45 V by the hold-off; on above u5_on, off below u5_on-0.35
        en5=0.45 if eng else vp*47/147
        if en5>u5_on: ild+=p_u5/max(vp,1.0)
        dvp=(iD-ild)/Cc*dt
        vg=min(vg+(ihg*dt+2.1e-9*dvp)/(2.1e-9+cgd+c_dvdt),vp+dvp+11.1); vp=max(vp+dvp,0.0)
        E+=iD*max(vds,0)*dt; av+=max(vds,0); ai+=iD; na+=1
        if na>=s10: trv.append(av/na); tri.append(ai/na); av=ai=0.0; na=0
        t+=dt
        if t>1e-3 and vp>Vb-0.3 and vg-vp>Vt+3.0: break      # Q2 fully enhanced: ohmic from here on
    sc=k.soa_check(np.array(trv),np.array(tri))
    return dict(E=E,t=t,soa=sc[0],tau=sc[1],t_eng=t_eng,t_u2off=t_u2off,t_u2on=t_u2on,u2=u2)

def ms(x): return '   -  ' if x is None else '%6.2f'%(x*1e3)

print('== 1. Hold-off threshold vs temperature (Vth = Vf(D401) + Veb(Q121) x 90k/22k)')
for c in (COLD,NOM,HOT): print('  %-20s Vf %.2f V, Veb %.2f V -> Vth %.2f V'%(c[0],c[1],c[2],vth(c)))
print('  Engage delay (HO_F 0 -> Q122 on, beta1 corner) for a step BAT_IN - VBAT_P = Vds at BAT_IN = Vb:')
for Vb in (8.0,13.8,24.0,32.0):
    row=[]
    for vds in (4.0,6.0,Vb):
        for c in (NOM,COLD):
            v=0.0; t=0.0
            while v<c[5] and t<5e-3: v+=(pnp_ic(min(vds,Vb),Vb,c,v)-v/100e3)/100e-9*1e-7; t+=1e-7
            row.append('%5.0f'%(t*1e6) if t<5e-3 else ' >5ms')
    print('  Vb %4.1f V: Vds 4 V %s / %s us, 6 V %s / %s us, full %s / %s us  (room / cold)'%(Vb,*row))
print('  Nuisance: a slot or bank inrush step is <= 224 A x 14 mOhm = 3.1 V for 2.7 us; slot kicks <= 1.8 us: both far below the')
print('  >= 46 us engage delay. Normal load (F1 10 A) through Q1 + Q2 hot (2 x 11 mOhm): 0.22 V << 2.47 V min threshold.')
print('  Cranking (VBAT_P > BAT_IN, Q1 blocks): D401 blocks the E-B junction (reverse <= Vds, MMBT5401 VEBO 6 V not reached).')
print('  Stress: Q121 VCE <= 57 V kick (150 V part); D402 reverse <= max(BB_UVLO 14.1 V, U5_EN 18.2 V) at 57 V (30 V part);')
print('  Q122 VCE <= 18.2 V + 0.3 V; Q122 sink <= beta x 1.4 mA (<= 140 mA), BAT54C 200 mA IF: C602 1 uF x 7.9 V discharge lasts <= 0.25 ms.')

print('\n== 2. Q2 cold start with the hold-off (U5 2.1 W bound and U2 70 W both held off until BAT_IN - VBAT_P < Vth; C602 from 0 V)')
print('  Vb     HGATE  corner  | Q2 E mJ  ramp ms  SOA ratio')
worst=0
for Vb in (12.0,13.8,24.0,28.8,32.0):
    for ihg in (39e-6,75e-6):
        for c in (COLD,HOT):
            r=run(Vb,ihg,c,vp0=0.0,warm=False); worst=max(worst,r['soa'])
            print('  %4.1f V %2.0f uA  %-5s  | %6.0f  %7.1f   %5.2f %s'%(Vb,ihg*1e6,c[0][:4],r['E']*1e3,r['t']*1e3,r['soa'],'OK' if r['soa']<=1 else 'EXCEEDED'))
print('  (Pass 6 review, no hold-off: 32 V cold start with U5 2.1 W = SOA ratio 1.17-1.43, EXCEEDED.)')

print('\n== 3. Q2 warm restart with the hold-off (C602 still charged; U2 70 W out, input <= 3.56 A; U5 2.1 W bound)')
print('  Start states: VBAT_P 4 V (U2 had stopped: restarts with soft start when VBAT_P > 3.8 V), Vb/2 (short dip: U2 still running at')
print('  FULL load at t = 0, harsher than the Pass 6 review model). HGATE 39 / 75 uA, hold-off cold (Vth 3.8 V, slow) and hot (2.5 V).')
print('  Vb   from    HGATE corner | engage ms  U2 off ms  U2 back ms | Q2 E mJ  SOA ratio')
for Vb in (12.0,13.8,24.0,28.8,32.0):
    for vp0,full in ((4.0,False),(Vb/2,True)):
        for ihg in (39e-6,75e-6):
            for c in (COLD,HOT):
                r=run(Vb,ihg,c,vp0=vp0,warm=True,u2_full=full); worst=max(worst,r['soa'])
                print('  %4.1f %5.1f V %2.0f uA %-4s | %s     %s     %s  | %6.0f   %5.2f %s'%(Vb,vp0,ihg*1e6,c[0][:4],ms(r['t_eng']),ms(r['t_u2off']),
                      ms(r['t_u2on']),r['E']*1e3,r['soa'],'OK' if r['soa']<=1 else 'EXCEEDED'))
print('  Same restarts WITHOUT the hold-off (reference, cold corner unused):')
for Vb in (24.0,32.0):
    for vp0,full in ((4.0,False),(Vb/2,True)):
        r=run(Vb,39e-6,NOM,vp0=vp0,warm=True,u2_full=full,holdoff=False,T=0.15)
        print('  %4.1f %5.1f V 39 uA no hold-off | Q2 E %5.0f mJ, SOA ratio %5.2f'%(Vb,vp0,r['E']*1e3,r['soa']))
print('  As first drawn with C602 = 10 uF (the Pass 5 delay cap) the hold-off needs 1.2-1.7 ms to pull U2 EN below 1.17 V; with U2 at full')
print('  load through a short dip Q2 is overstressed meanwhile, so C602 became 1 uF (same 0805 pad, C28323):')
for Vb in (24.0,32.0):
    r=run(Vb,39e-6,COLD,vp0=Vb/2,warm=True,u2_full=True,c602=11e-6)
    print('  %4.1f %5.1f V 39 uA cold, C602 10 uF | U2 off %s ms | SOA ratio %5.2f (EXCEEDED -> rejected)'%(Vb,Vb/2,ms(r['t_u2off']),r['soa']))
print('  C602 at its derated 0.5 uF (faster re-arm after release) at 32 V:')
for vp0,full in ((4.0,False),(16.0,True)):
    for c in (COLD,HOT):
        r=run(32.0,39e-6,c,vp0=vp0,warm=True,u2_full=full,c602=0.5e-6); worst=max(worst,r['soa'])
        print('  32.0 %5.1f V 39 uA %-4s | U2 back %s ms | SOA ratio %5.2f'%(vp0,c[0][:4],ms(r['t_u2on']),r['soa']))
print('  WORST SOA ratio with the hold-off, all corners: %.2f (%s)'%(worst,'OK' if worst<=1 else 'EXCEEDED'))
print('  U2 restart after release: C602 recharges from ~0.45 V to 1.17-1.29 V, tau 12-27 ms (24.8k x 0.5-1.1 uF):')
for Vb in (9.0,13.8,24.0,32.0):
    Vi=Vb*33/133
    a=12.4*math.log((Vi-0.45)/(Vi-1.17)); b=27.3*math.log((Vi-0.45)/(Vi-1.29))
    print('  %4.1f V: %5.1f-%5.1f ms after release (U2 then soft-starts over 7.5 ms)'%(Vb,a,b))
print('  Trade-off (documented): a BAT_IN dip below U1 UVLO (~5.2 V) now always restarts U2 (MCU runs on +3V3_SAFE via U5 / TPS2116 only')
print('  if VBAT_P stays above ~4.25 V); before, a short dip could ride through. At 70 W VBAT_P (230 uF) drains 10-25 V/ms, so U2 dropped')
print('  out anyway on any dip longer than ~1 ms: the change only affects sub-ms dips, and it is the price of a Q2 that survives them.')

print('\n== 4. M2: slot eFuse R_ILIM 3.09k (C22992, 1 %)')
lo=5.58*3.0/(3.09*1.01); hi=6.42*3.0/(3.09*0.99)
print('  TPS16630 I_OL = 18/R_ILIM(k) (SLVSET9G row at 3.0k: 5.58/6.00/6.42 A). UL 2367 recognition needs R_ILIM >= 3 kOhm:')
print('  3.09k -1 %% = %.3f k >= 3.0 k (3.01k would be 2.98k at -1 %%). I_OL %.2f-%.2f A incl. the resistor.'%(3.09*0.99,lo,hi))
print('  Channel short (TPS1HTC30 limit max 3.61 A): same-card preload still allowed %.2f A (4.02k: 0.53 A).'%(lo-3.61))
tauH=0.316*0.99*0.9*0.9*(1-0.013); tauR=0.195*0.99*0.9*0.9*(1-0.013)
def ttrip(I,I0,Ith,ta): return ta*math.log((I-I0)/(I-Ith)) if I>Ith else float('inf')
for m,I0,Ith,tau in (('HOT',2.4,3.15,tauH),('ROOM',4.0,5.11,tauR)):
    tt=ttrip(I0+hi,I0,Ith,tau)
    print('  %-4s bank overload trip, budget + one card at I_OL max: >= %.1f ms, FW 20 ms card cut margin %.1f ms'%(m,tt*1e3,tt*1e3-20))
I2=2*hi
print('  F1 10 A (74 A2s melt): two cards in limit = %.1f A until the bank trip (<= ~32 ms + 20 ms FW): %.1f A2s = %.0f %% of melt;'%(I2,I2**2*0.052,I2**2*0.052/74*100))
print('  steady-state the bank overload (ROOM 5.11-6.08 A, HOT 3.15-3.65 A) still caps the total far below F1.')
print('  Fast-trip 2 x I_OL = %.1f-%.1f A; hard short SCP 45 A / 1 us unchanged (kick_calc rerun with I_OL 6.30 A).'%(2*lo,2*hi))
print('  Hard short after the SCP retry: regulation at I_OL into a dead short = 32 V x %.2f A = %.0f W (4.02k: 156 W).'%(hi,32*hi))
print('  TPS16630 thermal: T_J reg 136-154 C, TSD 165 C; at ~200 W the die (RthJC ~1 C/W, ~0.15 J/K local) reaches TSD in ~0.5-1 ms,')
print('  the FET is TI-rated for this (power-limited start into short, SLVSET9G 9.3.2 / Fig. "start-up with short at 24 V, 3k").')
for I in (4.0,5.0,5.36):
    P=I*I*0.031*1.45
    print('  steady %.2f A: R_ON 31 mOhm x 1.45 hot = %.2f W -> T_J ~ %.0f F (%.0f C) at 149 F (65 C) ambient, RthJA 35 C/W'%(I,P,F(65+35*P),65+35*P))
print('  Steady current above 5.11 A (ROOM) trips the bank anyway, so the eFuse never sits at 6 A for long.')
print('  Connector: 9 VBAT contacts x 2 A (Pass 4 budget 6 A cont) >= 6.30 A; card SLn_VBAT sized for 6 A cont (slot_pinout_LV.csv).')

print('\n== 5. M3: engine slot feeds')
print('  U160 TPS2553DBVR, R_ILIM 210k: 110/130/150 mA (SLVS841 table), auto-retry. Engine card +3V3 load <= 15 mA (2x INA281,')
print('  TLV1812, EEPROM, 2.2k pull-ups): 7x margin. Fault on the card: +3V3_SAFE sees <= 150 mA extra, <= 0.55 A + 0.15 A = 0.70 A')
print('  on U5 backup (rated 0.6 A) only while +3V3 (U2 chain) is down at boot: possible brownout = safe state; on +3V3: 0.15 of 3 A.')
print('  U161 TPS16630 on the engine VBAT_P feed (chosen over the PTC that was drawn first):')
print('    R_ILIM 30k (C22984): I_OL 0.54/0.60/0.66 A (SLVSET9G row) -> 0.535-0.667 A with 1 % R vs <= 0.13 A load (LM317 + R47 10R = 125 mA).')
print('    SCP 45 A / 1 us: prospective short ~32 V / (0.06 Ohm source + harness) ~ 100+ A is cut in ~1 us: F1 I2t ~ 0.002 A2s;')
print('    Q1+Q2 drop 100 A x 22 mOhm = 2.2 V for ~1 us: far below the hold-off engage delay (>= 46 us).')
print('    PTC (LUTE 1812L030/60GR, rejected): I_max 40 A < ~100 A prospective (may fail), trip time 10s-100s of us at that current, during which')
print('    BAT_IN - VBAT_P ~ 2.2 V sits 0.3 V under the hot hold-off threshold: marginal, and a dead short could also restart U2.')
print('    Cost +$2.98 vs +$0.045 for the PTC; JLC stock 1824 (2026-11-24): 9 per board now. Auto-retry (MODE = GND, 648 ms).')
print('  Series R at U7 on the engine lines that had none: 10k 0805 (150 V) + BAT54S to +3V3_SAFE / GND on the MCU side.')
I=(36-3.3-0.3)/10e3
print('    36 V on a line: %.1f mA into the clamp, %.2f W in the 10k (0805 0.125 W... 0.11 W: OK at 149 F ambient with 0805 derating to 70 C = 100 %%)'%(I*1e3,I*I*10e3))
print('    ADC (FUEL_ISNS, CRANK_ISNS from INA281 outputs): 10k + U7 ADC Cs 5 pF + 1 nF C1111/C1112 at the pin:')
ke=5e-12/1.005e-9*math.exp(-1.6e-6/(10e3*1.005e-9))
print('      U7 ADC sample cap ~5 pF vs 1 nF at the pin: each conversion shares charge with the previous channel\'s voltage, error')
print('      <= %.2f %% of |V_prev - V_in| (%.0f LSB for a full-scale jump; the 10k recovers only 15 %% within a 64.5-cycle sample).'%(ke*100,4096*ke))
print('      Pass 7 m1 FW rule: convert FUEL/CRANK_ISNS twice back-to-back and use the second (error -> ~0), or sample >= 810.5 cycles')
print('      (20 us at 40 MHz = 2 tau: <= %.1f LSB).'%(4096*5e-12/1.005e-9*math.exp(-20e-6/(10e3*1.005e-9))))
print('  Pass 7 checks on the hold-off: BAT54C cross-leakage U5_EN -> BB_UVLO (reverse = 0.072 x VBAT_P: 0.36 V near the 5 V UVLO, where')
print('    hot leakage of a few uA moves BB_UVLO <= 0.05 V = 0.2 V of VBAT_P; at 32 V BB_UVLO sits at 7.9 V, far above 1.29 V): OK.')
print('    Q122 at high beta (300) could sink up to 0.42 A at first: C602 1 uF x 8 V = 8 uC, so <= ~20 us, inside the BAT54C 600 mA IFSM: OK.')
print('    BAT54S leakage hot: <= 2 uA at 3.3 V, 185 F (85 C) x 10k = 20 mV (0.6 % of 3.3 V full scale) on FUEL/CRANK_ISNS: covered by the')
print('    existing +/-2 % current-sense tolerance; cold/room < 1 mV.')
print('    Digital lines (MPU_GATE, MPU_SPEED, DPLUS_EXC_EN, DIAG_EN): 10k x (5 pF + 10 pF trace) = 0.15 us edges: MPU_SPEED <= 10 kHz OK.')
print('    DPLUS_SNS: 1k after D65 (card side 100k already): adds <= 0.1 % divider error.')
