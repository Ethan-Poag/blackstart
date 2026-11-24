#!/usr/bin/env python3
"""Pass 5 (Ethan 2026-11-23 10:20 PM HST): slot switches TPS48100 + 2x BSC070N10NS5 -> TPS16630 eFuse, U1 HGATE dV/dt network,
47R ahead of C225/U65. Every number below comes from the datasheets in docs/split_evidence/modular_pass5/ (tps1663.txt = TI SLVSET9G,
tps2663.txt = TI SLVSE94G, bsc070_soa.png) and the live JLC/LCSC searches in docs/split_evidence/modular_pass5/fetch/ (2026-11-23).
Transient numbers: docs/modular/tools/kick_calc.py (docs/modular/kick_calc.txt)."""
import math, json, os, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
F=lambda c: c*9/5+32
EV=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','split_evidence','modular_pass5','fetch')
def hdr(t): print('\n== '+t)
print(__doc__)

hdr('Part selection (JLC/LCSC live 2026-11-23; per board 8 + spares)')
def stock(fn,code):
    try:
        L=json.load(open(os.path.join(EV,fn)))['data']['componentPageInfo']['list'] or []
        for x in L:
            if x['componentCode']==code:
                pr=x.get('componentPrices') or []; return x.get('stockCount'),(pr[0]['productPrice'] if pr else None)
    except Exception: pass
    return None,None
for fn,code,name,verdict in (
    ('search_TPS16630PWPR.json','C1849461','TPS16630PWPR (HTSSOP-20 PWP)','CHOSEN: adjustable UVLO + OVP cut-off (no clamp), I_OL 0.6-6 A, latch or retry, best stock and price'),
    ('search_TPS26631PWPR.json','C2866319','TPS26631PWPR (same PWP footprint)','pin-compatible alternate: pins 4/5 B_GATE/DRV open, 6 IN_SYS = IN, 16 PGTH (tie to the fault line), 17 PGOOD open; stock 1 only'),
    ('search_TPS26631.json','C1850273','TPS26631RGER (VQFN-24)','function-compatible second source (same die family, different footprint): needs a layout variant'),
    ('search_TPS26632.json','C1850278','TPS26632RGER','REJECTED: fixed OV clamp 32/32.8/35 V above 35 V with 162 ms timeout -> slot cut inside the 32-36 V rating'),
    ('search_TPS26636.json','C1849494','TPS26636PWPT','REJECTED: OV clamp 35.7/36.6/39 V (min below the 36 V / 60 s rating)'),
    ('search_MAX17613.json','C3198160','MAX17613AATP+','REJECTED: 3 A max < 4.0 A ROOM slot budget'),
    ('search_TPS2660.json','C544399','TPS26600PWPR','REJECTED: I_LIM 2.23 A max < 4.0 A ROOM slot budget'),
    ):
    s,p=stock(fn,code) if code else (None,None)
    print('%-38s %-9s stock %-6s $%-7s %s'%(name,code or '-',s if s is not None else '-',p if p is not None else '-',verdict))
print('Second source as fitted: TPS26631PWPR drops into the same land pattern (pin 16 PGTH to SLn_PWR_FAULT_N, pin 17 PGOOD unused ->')
print('start-into-short is then reported by FLT# only, after t(Treg_timeout) 1.1-1.5 s). TPS26631RGER (217 in stock) is the volume second source')
print('but needs a VQFN-24 footprint variant (layout frozen now: noted as a layout-time option, not done).')

hdr('TPS16630 settings (SLVSET9G 6.5 / 6.6)')
Rt,Rb=100e3,27e3
print('UVLO 100k/27k (kept, 1 %%): on %.2f V (%.2f-%.2f), off %.2f V (%.2f-%.2f); UVLO_toff 9-16 us; leakage 150 nA x 21k = 3 mV'%(
    1.2*(Rt+Rb)/Rb,1.176*(Rt*0.99+Rb*1.01)/(Rb*1.01),1.224*(Rt*1.01+Rb*0.99)/(Rb*0.99),1.122*(Rt+Rb)/Rb,1.09*(Rt*0.99+Rb*1.01)/(Rb*1.01),1.15*(Rt*1.01+Rb*0.99)/(Rb*0.99)))
Ot,Ob=453e3,10e3
ovr=(1.176*(Ot*0.99+Ob*1.01)/(Ob*1.01),1.2*(Ot+Ob)/Ob,1.224*(Ot*1.01+Ob*0.99)/(Ob*0.99)); ovf=(1.09*(Ot*0.99+Ob*1.01)/(Ob*1.01),1.122*(Ot+Ob)/Ob,1.15*(Ot*1.01+Ob*0.99)/(Ob*0.99))
print('OVP 453k/10k: off rising %.1f/%.1f/%.1f V, back on below %.1f/%.1f/%.1f V; OVP_toff 8.5-14 us, re-on 150 + 49.5 x 10 = 645 us + dVdT ramp'%(ovr+ovf))
print('   -> never trips inside the 9-32 V / 36 V-60 s rating (min %.1f V); cuts a slot before card parts rated 60-62 V see sustained OV (max %.1f V).'%(ovr[0],ovr[2]))
print('   Trip-kick exposure of healthy slots above %.1f V: <= 1.8 us (kick_calc pessimistic corner) << OVP_toff min 8.5 us -> no nuisance OVP.'%ovr[0])
print('ILIM 4.02k: I_OL 4.185/4.500/4.815 A (datasheet row at 4.02k, VIN-VOUT 1 V); with 1 %% R: %.3f-%.3f A >= 4.0 A ROOM budget (margin %.0f mA)'%(4.185/1.01,4.815/0.99,(4.185/1.01-4.0)*1e3))
IOLMAX=4.815/0.99
print('Fast-trip 2 x I_OL = %.1f-%.1f A (soft short 2.2-4.5 us); I(SCP) 45 A typ, hot-short response 1 us typ; then I_OL regulation'%(2*4.185/1.01,2*IOLMAX))
sr=(1.775*23.5/10e-9/1.1,2*25/10e-9,2.225*26/10e-9/0.9)
print('dVdT 10 nF (+/-10 %%): %.2f/%.2f/%.2f V/ms -> 32 V in %.1f/%.1f/%.1f ms; card load 2.76 uF -> %.0f mA max inrush'%(sr[0]/1e3,sr[1]/1e3,sr[2]/1e3,32/sr[2]*1e3,32/sr[1]*1e3,32/sr[0]*1e3,2.76e-6*sr[2]*1e3))
ton=(742+49.5*10)*1e-6
pg=1.5*ton+32/sr[0]+13e-3
print('PGOOD high after SHDN# high: delay %.2f ms (x1.5 margin) + ramp %.1f ms + deglitch 13 ms max = %.1f ms << C2.3 150 ms charging mask'%(ton*1e3,32/sr[0]*1e3,pg*1e3))
print('IMON 15k: %.3f V/A typ; %.2f V at I_OL max (gain 29.58 uA/A); pin abs max 5.5 V. Test point only (no ADC channel; layout frozen).'%(27.9e-6*15e3,IOLMAX*29.58e-6*15e3))
print('SHDN#: internal pull-up (open 2.48-3.3 V, 10 uA): NEW 10k pull-down on SLn_PWR_EN -> <= 0.10 V if the 1G02 is unpowered/open (V_SHUTF 0.8 V);')
print('   1G02 drive 3.3 V / 10k = 0.33 mA. Abs max SHDN 5.5 V (3.3 V logic).')
print('FLT# and PGOOD (open drain, 36-130 ohm, 10 mA) wired-OR with the TPS2553 FAULT onto SLn_PWR_FAULT_N (10k to +3V3_SAFE: 0.33 mA, VOL <= 43 mV).')
print('MODE open = latch: current limit > t_CL 129/162/202 ms, TSD, -> OFF until SHDN# or UVLO toggles (FW: EN_N high >= 20 ms).')

hdr('Fault behaviour seen on SLn_PWR_FAULT_N (FW C5.1)')
for a,b in (('slot off (SHDN# low)','PGOOD low -> line LOW: invalid, masked (N8) - unchanged rule'),
            ('enable into a healthy card','line LOW for <= %.0f ms (PGOOD rising deglitch) then HIGH: inside the 150 ms C2.3 mask'%(pg*1e3)),
            ('hard short while running','1 us SCP trip, then I_OL regulation; FLT# LOW after 1.09-1.6 ms; TSD (ms, Fig 6-13) -> latched OFF, PGOOD LOW'),
            ('overload > I_OL (soft)','I_OL regulation, FLT# LOW after 1.09-1.6 ms; latch at 129-202 ms or TSD; FW cuts EN_N at the first FLT#'),
            ('enable into a short','thermal regulation T_J 136-154 C (277-309 F) for 1.1-1.5 s, PGOOD never rises -> line stays LOW -> C2.3 250 ms timeout -> SLOT_SHORT_LOCKOUT'),
            ('VBAT_SLOTS > OVP (53.4-57.8 V)','FET off in 8.5-14 us, FLT# LOW; auto-on below 49.5-53.9 V: all slots at once -> C7.9 supply event (VBAT_P INA237 high)'),
            ('VBAT_SLOTS < UVLO (5.13-5.44 V)','FET off, FLT# LOW: all slots at once -> C7.9 supply dip'),
            ('ILIM pin open/short','FET off, FLT# LOW -> CARD_FAULT on that slot (board fault, service)')):
    print('  %-34s %s'%(a,b))

hdr('Coordination: slot vs bank (U110 kept) vs F1 (10 A, melt I2t >= 115 A2s)')
tauH=0.316*0.99*0.9*0.9*(1-0.013); tauR=0.195*0.99*0.9*0.9*(1-0.013)
def ttrip(I,I0,Ith,ta): return ta*math.log((I-I0)/(I-Ith))
for m,I0,Ith,tau in (('HOT',2.4,3.15,tauH),('ROOM',4.0,5.11,tauR)):
    told=ttrip(I0+2*3.61,I0,Ith,tau); tnew=ttrip(I0+IOLMAX,I0,Ith,tau); t1=ttrip(I0+3.61,I0,Ith,tau)
    print('m9 %s: card capped at I_OL max %.3f A by its eFuse: bank overload trip >= %.1f ms (was %.1f ms for two channels at 3.61 A each; one channel %.1f ms)'%(m,IOLMAX,tnew*1e3,told*1e3,t1*1e3))
    print('     -> FW ">1 channel faulted = cut card by 20 ms" keeps %.1f ms margin (was %.1f); the eFuse FLT# (<= 1.6 ms) normally cuts the card first.'%((tnew-20e-3)*1e3,(told-20e-3)*1e3))
print('Overload selectivity: eFuse FLT# 1.09-1.6 ms -> FW cut (C5.1, first scan) << bank overload trip >= %.1f ms; eFuse self-latch 129-202 ms is the'%(min(ttrip(2.4+IOLMAX,2.4,3.15,tauH),ttrip(4+IOLMAX,4,5.11,tauR))*1e3))
print('   no-FW backstop for a dead short (TSD in ms); for a soft overload with FW dead the bank overload cutoff (hardware) trips first: safe, not selective.')
print('Hard-short selectivity: slot SCP 1 us typ (soft 2.2-4.5 us) vs bank U110 SCP 21.2 A min with t_SC 466 us min -> > 100x; bank never trips on a slot short.')
import kick_calc as k
worst={}
for V in (24.0,28.8,32.0):
    for cap,lab in ((None,'pessimistic (no FET saturation, current free for t_resp)'),(60.0,'realistic (FET saturates ~60 A)')):
        r=k.run_ef(V,Cs_slot=2.2e-6,Lbank=150e-9,t_resp=1.5e-6,ipk_cap=cap,T=60e-6,dt=2e-9); p=r['pk']
        worst[(V,cap)]=r
        print('slot dead short at %4.1f V, %-55s F1 I2t %.4f A2s (%.0fx below 115 A2s), eFuse peak %3.0f A, harness pk %3.0f A, eFuse energy %.1f mJ'%(
            V,lab,r['I2t'].max(),115/r['I2t'].max(),p['ief'].max(),p['iL'].max(),r['E_ef'].max()*1e3))
print('Bank FETs (Q106/Q107) carry the slot peak for ~2 us: (0.55 x 363 A)^2 x 11.5 mOhm = %.0f W x ZthJC(2 us) 0.012 K/W = %.0f K (negligible).'%((0.55*363)**2*0.0115,(0.55*363)**2*0.0115*0.012))
print('Residual (not a card fault, unchanged from Pass 4): a dead short ON VBAT_SLOTS itself (mainboard bus) is cleared by F1 (74-115 A2s at')
print('   ~0.18-0.28 ms) before the U110 latch (466 us min) - see pass4_calc.txt. Every card-side short is now upstream-isolated by an eFuse.')

hdr('eFuse thermal, hard short at 32 V (Tc 149 F / 65 C board)')
print('After the 1 us trip the eFuse regulates I_OL: P = (32 - 0) x %.2f A = %.0f W -> TSD 165 C (329 F) typ in the ms range (SLVSET9G Fig 6-13),'%(IOLMAX,32*IOLMAX))
print('   transient T_J limit = T(TSD) (6.1 Abs Max), then latched OFF (MODE open). FLT# asserts at TSD or at 1.09-1.6 ms, whichever is first.')
print('Start into a short: thermal regulation T_J(REG) 136/145/154 C (277/293/309 F) for 1.1/1.25/1.5 s, then latched OFF (FLT#).')
print('Trip-kick energy into the eFuse (120 us window incl. I_OL phase): <= %.1f mJ; SS310B freewheel: <= %.2f mJ (IFSM 80 A / 8.3 ms).'%(
    max(r['E_ef'].max() for r in worst.values())*1e3,max(r['E_sch'].max() for r in worst.values())*1e3))
print('OUT negative excursion: clamped by SS310B at -%.1f V (model Vf at high current) for a few us; TI SLVSET9G 9.4.1 / 9.5 prescribe exactly this'%(-min(r['pk']['vout_neg'].min() for r in worst.values())))
print('   Schottky for the -0.3 V OUT rating under inductive turn-off (place at the OUT/GND pins: layout note).')

hdr('U65 feed: D120 -> 47R 1206 (R1002) -> C225 10 uF / U65 TPS7B6950 (IN abs max 45 V)')
print('DC: 5 mA x 47R = %.2f V drop, %.1f mW (1206 rating 250 mW); RC 47R x 10 uF = 470 us vs the us-scale kick -> U65 IN <= 31.8 V at 32 V'%(5e-3*47,25e-6*47*1e3))
print('Cold crank 9 V: 9 - 0.45 (D120) - 0.24 = 8.3 V at U65 IN (LDO 5 V needs >= ~5.5 V). Surge 36 V / 60 s: U65 IN <= 35.6 V < 40 V operating.')
print('Inrush at power-up: C225 charge peak <= 32/47 = 0.68 A for ~0.5 ms: 47R pulse energy 1/2 C V^2 = %.1f mJ (1206 pulse rating >> this).'%(0.5*10e-6*32**2*1e3))

hdr('U1 HGATE network (C601 22 nF / 100 V + R1001 1k) - see kick_calc.txt hot-plug table for Q2 SOA and Tj')
print('I_INRUSH = I_HGATE x C_OUT / CdVdT: C_OUT ~230 uF (2x100 uF + ceramics) -> 39/55/75 uA -> %.2f/%.2f/%.2f A no load; ramp to 32 V %.1f-%.1f ms'%(
    39e-6*230e-6/22e-9,55e-6*230e-6/22e-9,75e-6*230e-6/22e-9,32*24.1e-9/75e-6*1e3,32*24.1e-9/39e-6*1e3))
print('Turn-off: HGATE sinks 168 mA; through 1k the 22 nF can return <= 45 mA -> Q2 still off in ~0.2 us after the OV deglitch (kick_calc adds 1 us).')
print('CdVdT discharge to the source level through 1k: tau 22 us; after an OV cut Q2 re-conducts as a follower once VBAT_P sags ~3-5 V.')
print('C601 voltage: <= VBAT_P + 11 V (HGATE clamp) ~ 47-58 V on transients vs 100 V rating.')
