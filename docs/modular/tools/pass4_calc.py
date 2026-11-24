"""Pass 4 review fixes (review modular_pass4: P4-MAJ-1, m1..m9). Every number in MODULAR_ARCHITECTURE section 16 and the Pass 4 rows
of FW_REQ_CARDS / INSTALL_SAFETY comes from this script.  Run from the repo root:
    python3 docs/modular/tools/pass4_calc.py > docs/modular/pass4_calc.txt
Sources: TI TPS4810-Q1 SLUSEW1C (docs/split_evidence/modular_pass1/tps48100-q1_SLUSEW1C.txt), TI SFFS636 pin FMA and E2E threads
(docs/split_evidence/modular_pass4/), BSC070N10NS5 rev 2.3 Diagram 4 (ZthJC single pulse, read off the curve), TCA9555 SCPS200,
TS5A3166 SCDS186E, 1N4148W (C81598). The battery/harness/VBAT_P dead-short model is the Pass 4 reviewer's /tmp/p4/hardshort12.py
(same topology and parameter grid), extended with the per-controller VS hold-up, UVLO RC nodes, bank SCP timer, the SMBJ33CA on
VBAT_P and the FET junction-temperature convolution. Temperatures in F (C in parentheses)."""
import math, itertools, os
F=lambda c:c*9/5+32
def hdr(t): print('\n== '+t)

# ---------------- SLUSEW1C constants ----------------
VS_SCP_MIN=4.0            # 5.3 minimum VS for short-circuit protection
VS_PORF=(1.7,2.33,3.06)   # 5.5 V(S_PORF)
IQ_MAX=49e-6; IBST_MAX=510e-6; IBST_MIN=190e-6
I_VS=IQ_MAX+IBST_MAX      # worst VS draw: quiescent + charge pump running
ITMR=(67e-6,87e-6,114e-6); VTMR_SC=(0.924,1.1,1.21); ITMR_FLT=(1.4e-6,2.73e-6,4.8e-6); VTMR_LOW=(0.148,0.21,0.25)
T_PROP=4.3e-6             # tSC propagation delay (max, C_TMR open)
VBST_UVLOR=(8.0,9.0,9.93); VBST_UVLOF=(7.28,8.2,8.93); VG1GOOD=(5.47,7.0,8.33)
UVLOF=(1.083,1.138,1.19); ENF=0.292

def tmr(C,tol=0.05,R=100e3):
    f=lambda c,i,v: R*c*math.log(1/(1-v/(R*i)))
    return f(C*(1-tol),ITMR[2],VTMR_SC[0]),f(C,ITMR[1],VTMR_SC[1]),f(C*(1+tol),ITMR[0],VTMR_SC[2])
def tmr_x7r(C): return tmr(C,tol=0.19)   # X7R -10 % tol, -10 % temp (Pass 3 basis)
TSC_1N_MAX=tmr(1.0e-9)[2]   # chosen slot C_TMR, max t_SC
hdr('TI SLUSEW1C findings used for P4-MAJ-1 (exact datasheet lines are quoted in MODULAR_ARCHITECTURE section 16.1)')
print('6.1/5.1 Abs max: VS, CS+, CS- each -65..100 V to GND; SRC -65..100 V to GND; CS+ to CS- -1..100 V; BST/G1PU/G1PD to SRC -0.3..19 V.')
print('        No VS-to-CS+, VS-to-CS- or VS-to-SRC rating exists: VS = 32 V with CS+ = CS- = SRC = 0 V is inside the abs max table.')
print('        Fig 7-6 (low-side sensing) itself runs VS = 48 V with CS+/CS- near GND; SFFS636 Table 4-2: CS- or SRC shorted to GND =')
print('        "Short to GND protection starts" (normal function with VS powered).')
print('5.3 ROC: VS 3.5..95 V; minimum VS for short-circuit protection 4 V; VS and SRC caps >= 22 nF; BST-SRC cap >= 0.1 uF (no maximum).')
print('5.5: VS POR falling 1.7/2.33/3.06 V; IQ 35/49 uA; I(BST) 190/345/510 uA; BST UVLO rising 8/9/9.93 V, falling 7.28/8.2/8.93 V.')
print('7.3.3.2: 100k across C_TMR = latch-off; reset by INP1, EN/UVLO < V(ENF) or VS below V(VS_PORF).')
print('8.3: "TI recommends to place a RVS - CVS filter ... RVS value around 100 ohm"; Fig 8-11 D1 is the input TVS (no series diode drawn).')
print('E2E 1298005 (TI, TPS4811-Q1 sibling): 300 ohm in series with VS "should be ok ... Please use with 1uF cap at Vs".')
print('NOT specified anywhere: the CS+/CS- common-mode range of the SCP comparator in high-side mode (CS_SEL = GND) -> bench test 16.6 #1.')

# ---------------- P4-MAJ-1 (a): VS hold-up ----------------
hdr('P4-MAJ-1: per-controller VS hold-up  D (1N4148W) -> 100R -> VS, C_VS 1 uF / 100 V X7R 1206 (CL31B105KCHNNNE) to GND')
# C_VS effective. Samsung's product server returned "Server Error" today (DC-bias curve not fetchable); use a deliberately
# pessimistic bound: -40 % at 32 V, -15 % at 12 V DC bias, -10 % tolerance, -10 % temperature, -5 % aging.
def cvs_eff(V): return 1e-6*(1-(0.15+(0.40-0.15)*max(0,min(1,(V-12)/20))))*0.9*0.9*0.95
VF=0.75; RVS=100.0; ID_LEAK_HOT=50e-6   # 1N4148W Vf at ~1 mA hot-cold bound; reverse leakage bound at 302 F (150 C)
for V0 in (12.6,24.0,28.8,32.0):
    v=V0-VF-RVS*I_VS; c=cvs_eff(V0); t=c*(v-VS_SCP_MIN)/(I_VS+ID_LEAK_HOT)
    print('%4.1f V: VS starts at %.2f V, C_VS eff %.3f uF, hold-up to 4.0 V = %.1f ms (draw %.0f uA + %.0f uA diode leakage)'%(V0,v,c*1e6,t*1e3,I_VS*1e6,ID_LEAK_HOT*1e6))
print('-> >= %.1f ms of guaranteed VS >= 4 V vs a slot latch <= %.1f us: > 100x margin'%(cvs_eff(12.6)*(12.6-VF-RVS*I_VS-4)/(I_VS+ID_LEAK_HOT)*1e3,(TSC_1N_MAX+T_PROP)*1e6))
print('VS steady drop: Vf + 100R x %.0f uA = %.2f V below the feed; RVS power %.0f uW'%(I_VS*1e6,VF+RVS*I_VS,RVS*I_VS**2*1e6))
print('C_VS recharge after the latch (feed back up within us): tau = 100R x 1 uF = 100 us; diode peak at bank turn-on <= 32 V/100R = 0.32 A (IFSM 1 A @ 1 s)')
print('Voltage stress: VBAT_P clamp SMBJ33CA 53.3 V @ 11.3 A (D1 SMDJ36CA ~58 V upstream) -> C_VS rated 100 V; 1N4148W VRRM 75 V vs reverse <= VS - VBAT_SLOTS <= 58 V')
print('Feed choice (16.1): slots from VBAT_SLOTS, bank U110 from VBAT_P. Bank off -> slot VS = 0 (POR, 0 uA from VBAT_P); 8 x VBAT_P feeds would cost')
print('   8 x I(SHDN) 4.6 uA = %.0f uA parked plus 8 x diode leakage and keep the slot controllers powered with CS+ = 0 V. Both satisfy 5.1.'%(8*4.6))

# ---------------- C_TMR ----------------
hdr('C_TMR with 100k latch-off (SLUSEW1C Eq 9 form t = R C ln(1/(1 - V_TMR_SC/(R I_TMR)))), C0G +/-5 %, no bias/temperature drift')
BANK=tmr_x7r(68e-9)   # -10 % tol AND -10 % temperature (Pass 3 quoted 517 us with tolerance only)
opts={'4.7 nF X7R (Pass 3)':tmr_x7r(4.7e-9),'1.5 nF C0G':tmr(1.5e-9),'1.0 nF C0G':tmr(1.0e-9)}
for k,(a,b,c) in opts.items():
    print('%-20s t_SC %.1f / %.1f / %.1f us (+%.1f us prop = latch <= %.1f us); bank 68 nF min %.0f us -> time grading %.1fx'%(k,a*1e6,b*1e6,c*1e6,T_PROP*1e6,(c+T_PROP)*1e6,BANK[0]*1e6,BANK[0]/(c+T_PROP)))
print('latch-off check: after the trip TMR charges at I(TMR_SRC_FLT) max 4.8 uA x 100k = %.2f V < V(TMR_SC) min 0.924 V -> counter never advances (independent of C)'%(4.8e-6*100e3))
print('inrush immunity: SCP is gated by G1_GOOD (5.47 V min). The load-charging Miller plateau ends below it:')
for lab,K,Vt,I in (('slow corner 11.6 A, Vt 3.82 V, K 36',36,3.82,11.6),('fast corner 36 A, Vt 2.86 V, K 30',30,2.86,36.0)):
    vp=Vt+math.sqrt(I/2/K); print('   %s: plateau Vgs %.2f V < G1_GOOD min 5.47 V -> SRC ramp done before the comparator is looked at'%(lab,vp))

# ---------------- dead-short model ----------------
ZTH=[(1e-6,0.0085),(3e-6,0.016),(1e-5,0.040),(3e-5,0.085),(1e-4,0.195),(3e-4,0.36),(1e-3,0.545),(1e-2,1.16),(1e-1,1.49)]  # BSC070N10NS5 Diagram 4, single pulse, max
def zth(t):
    if t<=0: return 0.0
    if t<=ZTH[0][0]: return ZTH[0][1]*(t/ZTH[0][0])**0.64
    for (t1,z1),(t2,z2) in zip(ZTH,ZTH[1:]):
        if t1<=t<=t2: return math.exp(math.log(z1)+(math.log(z2)-math.log(z1))*(math.log(t)-math.log(t1))/(math.log(t2)-math.log(t1)))
    return ZTH[-1][1]
def tj_rise(P,dt):
    """superposition of ZthJC steps; P sampled every dt; returns peak rise (case held at the start temperature)"""
    pk=0.0; n=len(P)
    Z=[zth((k+0.5)*dt) for k in range(n+1)]
    for m in range(n):
        s=0.0; prev=0.0
        for k in range(m+1):
            dp=P[k]-prev; prev=P[k]; s+=dp*Z[m-k]
        pk=max(pk,s)
    return pk
RDS25=7e-3                                      # max at 25 C
def rds(tj): return RDS25*(1+0.0064*(tj-25))    # ~1.8x at 150 C (Diagram 9 shape)
SHARE=0.55                                      # hot FET share of two paralleled FETs (RDS(on) spread)
def run(Vb,Rb,Lb,ESRe,Rd2,t_latch,feed='slots',Rup=0.013,Cc=32e-6,Ce=200e-6,Rd1=0.010,Cs=0.9e-6,Ls=50e-9,T=400e-6,dt=5e-9,Tc0=65.0):
    """Ls = slot loop inductance (slot FETs + DIN contacts + card copper to the short); 50 nH is the stiff bound."""
    iL=0.0; i2=0.0; ilatch=0.0; vC=vE=vS=Vb; vvs=Vb-VF-RVS*I_VS; vvb=vvs        # slot VS, bank VS
    tau_min=100e3*27e3/127e3*4.7e-9*0.81; k=27/127
    vu_s=vS*k; vu_b=vC*k                                  # slot UVLO node (all slots: fed by VBAT_SLOTS), bank UVLO (VBAT_P)
    t=0.0; I2t=0.0; on=1.0; latched=None
    r=dict(vrev=0.0,iL_latch=0.0,t320=0.0,vs_min=99,vb_min=99,vuS_min=99,vuB_min=99,ibank_over=0.0,ibank_run=0.0,ipk=0,vp_max=0,vslots_min=99,uvlo_before_latch=False,vs_below4=False)
    P=[]; Pb=[]; samp=int(round(0.1e-6/dt))
    i=0
    while t<T:
        vp=vC
        i1=(vp-vS)/Rd1
        if latched is None: i2+=(vS-i2*Rd2)/Ls*dt
        else: i2=ilatch*on
        iE=(vE-vp)/ESRe
        itvs=(vp-36.7)/1.47 if vp>36.7 else 0.0
        iL+=(Vb-iL*(Rb+Rup)-vp)/Lb*dt
        vC+=(iL+iE-i1-itvs)/Cc*dt; vE+=-iE/Ce*dt; vS+=(i1-i2)/Cs*dt
        feedv=vS if feed=='slots' else vp
        ich=(feedv-VF-vvs)/(RVS+6.0) if feedv-VF>vvs else 0.0
        vvs+=(ich-I_VS)/1e-6*dt if vvs>0 else 0.0
        ichb=(vp-VF-vvb)/(RVS+6.0) if vp-VF>vvb else 0.0
        vvb+=(ichb-I_VS)/1e-6*dt if vvb>0 else 0.0
        vu_s+=(vS*k-vu_s)/tau_min*dt; vu_b+=(vp*k-vu_b)/tau_min*dt
        I2t+=iL*iL*dt
        if latched is None:
            r['vs_min']=min(r['vs_min'],vvs); r['vslots_min']=min(r['vslots_min'],vS)
            if vvs<VS_SCP_MIN: r['vs_below4']=True
            if vu_s<UVLOF[2]: r['uvlo_before_latch']=True
            if t>=t_latch: latched=t; ilatch=i2; r['iL_latch']=iL
        else:
            on=max(0.0,1.0-(t-latched)/0.5e-6)          # G1PD 2 A turn-off ~0.5 us
        r['vb_min']=min(r['vb_min'],vvb); r['vuS_min']=min(r['vuS_min'],vu_s); r['vuB_min']=min(r['vuB_min'],vu_b)
        if SHARE*i2>320: r['t320']+=dt
        r['vrev']=max(r['vrev'],vvs-vS)
        r['ipk']=max(r['ipk'],i2); r['vp_max']=max(r['vp_max'],vp)
        if i1>21.2: r['ibank_run']+=dt; r['ibank_over']=max(r['ibank_over'],r['ibank_run'])
        else: r['ibank_run']=0.0
        if i%samp==0 and t<=t_latch+1e-6:
            P.append((SHARE*i2)**2*rds(Tc0+60)); Pb.append((SHARE*i1)**2*rds(Tc0+60))
        t+=dt; i+=1
    r['I2t']=I2t; r['dTj']=tj_rise(P,0.1e-6); r['dTjb']=tj_rise(Pb,0.1e-6)
    r['E_fet']=sum(P)*0.1e-6
    return r
FAST=os.environ.get('P4_FAST')
GRID=list(itertools.product([0.015,0.035],[0.5e-6,2e-6],[0.08,0.25],[0.012,0.025]))
if FAST: GRID=GRID[:2]
for lab in ('4.7 nF X7R (Pass 3)','1.5 nF C0G','1.0 nF C0G'):
    tl=opts[lab][2]+T_PROP
    hdr('Dead slot short, slot latch at t_SC max + prop = %.1f us (%s), VS hold-up fitted, Tc 149 F (65 C) start, hot FET %.0f %% share'%(tl*1e6,lab,SHARE*100))
    print('grid per VBAT: Rb 15/35 mOhm x Lb 0.5/2 uH x electrolytic ESR 80/250 mOhm x Rd2 12/25 mOhm (reviewer grid), slot loop 50 nH; F1 melt 115 A2s (77 F) / ~74 A2s (149 F)')
    for Vb in (12.6,24.0,28.8,32.0):
        R=[run(Vb,*g,tl) for g in GRID]
        w=lambda key,f=max: f(x[key] for x in R)
        print('%4.1f V: slot VS min %.2f V (>= 4 V: %s) | VBAT_SLOTS min %.2f V | slot UVLO node min before latch -> %s | bank VS min %.2f V | bank UVLO node min %.2f V (UVLOF max 1.19 V) | bank I>21.2 A for <= %.0f us (bank latch needs >= %.0f us) | VBAT_P peak %.1f V | F1 I2t <= %.1f A2s | slot current pk %.0f A | hot FET dTj <= %.0f K (bank FET %.0f K), E %.0f mJ | harness current at latch <= %.0f A | VS diode reverse <= %.1f V'%(
            Vb,w('vs_min',min),'YES' if not any(x['vs_below4'] for x in R) else 'NO',w('vslots_min',min),
            'UVLO trips first (HICCUP)' if any(x['uvlo_before_latch'] for x in R) else 'never below 1.19 V',
            w('vb_min',min),w('vuB_min',min),w('ibank_over')*1e6,BANK[0]*1e6,w('vp_max'),w('I2t'),w('ipk'),w('dTj'),w('dTjb'),w('E_fet')*1e3,w('iL_latch'),w('vrev')))
print('\nNotes: VBAT_SLOTS goes below 0 V in the lumped model (undamped 50 nH / 0.9 uF ring); the UVLO RC and the VS diode ride through it. VBAT_P peak is the\n'
      '   harness energy (1/2 Lb I^2) dumped into VBAT_P ceramics/electrolytic ESR/SMBJ33CA (linear 1.47 ohm above 36.7 V) when the slot latches: < 100 V\n'
      '   (TPS48100, BSC070, C_VS ratings) but above 40 V parts on VBAT_P -> the pre-existing VBAT_P surge open item (DESIGN_NOTES) now has a defined source;\n'
      '   a shorter latch lowers it (it was larger with the bank-only latch).')
print('Without the hold-up (Pass 3) the reviewer measured slot VS 0.70-3.14 V at 12.6 V for most of the 103 us window and 33-93 A2s on F1.')

# ---------------- VBAT_P overshoot sensitivity (open item) ----------------
hdr('VBAT_P overshoot at the slot latch (1.0 nF), worst of the grid, by clamp model (OPEN ITEM, bench test 16.7 #6)')
_SRC=open(__file__).read(); _CUT=_SRC.index("FAST=os.environ.get('P4_FAST')")
_BASE=_SRC[_SRC.index('# ---------------- dead-short model'):_CUT]
for lab,expr in (('SMBJ33CA only (as above)',"(vp-36.7)/1.47 if vp>36.7 else 0.0"),
                 ('+ D1 SMDJ36CA at BAT_IN (40 V, 0.35 ohm)',"((vp-36.7)/1.47 if vp>36.7 else 0.0)+((vp-40.0)/0.35 if vp>40.0 else 0.0)"),
                 ('SMBJ33CA -> SMDJ33CA 3 kW, + D1',"((vp-36.7)/0.295 if vp>36.7 else 0.0)+((vp-40.0)/0.35 if vp>40.0 else 0.0)")):
    g=dict(globals()); exec(_BASE.replace("(vp-36.7)/1.47 if vp>36.7 else 0.0",expr),g)
    out=[]
    for Vb in (24.0,28.8,32.0):
        pk=max(g['run'](Vb,Rb,Lb,E,Rd,TSC_1N_MAX+T_PROP,T=150e-6,dt=1e-8)['vp_max'] for Rb,Lb,E,Rd in GRID)
        out.append('%.1f V -> %.1f V'%(Vb,pk))
    print('%-42s %s'%(lab,' | '.join(out)))
print('VBAT_P ratings: LM5176 55 V, LMR36506 65 V, TPS1HTC30 (U68) 64 V, LM74800 (U1) 70 V, INA237 85 V, 50 V electrolytic/MLCCs on VBAT_P.')
print('-> at a 24 V battery the peak sits at the 50 V capacitor ratings; at 28.8-32 V it exceeds LM5176 55 V. Not fixed in Pass 4: needs a decision')
print('   (stronger VBAT_P clamp sized for 1/2 Lb I^2 ~0.3 J, slower slot turn-off, or a battery-voltage limit) and the bench measurement.')

# ---------------- m1 ----------------
hdr('m1: on-state dead short at 32 V, Tc 149 F (65 C): hot FET 55 %% share, RDS(on) %.1f mOhm at Tj 125 C, ZthJC Diagram 4 (max) superposition'%(rds(125)*1e3))
for lab in opts:
    tl=opts[lab][2]+T_PROP
    R=[run(32.0,0.015,0.5e-6,0.08,0.012,tl),run(32.0,0.015,0.5e-6,0.08,0.025,tl)]
    for x,rd in zip(R,(12,25)):
        tj=65+x['dTj']
        print('%-20s Rd2 %2d mOhm: latch %.1f us, pk slot current %.0f A (hot FET %.0f A vs ID,pulse 320 A), above 320 A for %.2f us, E %.0f mJ, dTj %.0f K -> Tj %.0f F (%.0f C) vs Tj max 302 F (150 C)'%(
            lab,rd,tl*1e6,x['ipk'],SHARE*x['ipk'],x['t320']*1e6,x['E_fet']*1e3,x['dTj'],F(tj),tj))
print('ID,pulse 320 A is the Diagram 3 package line (Tc 77 F). CHOSEN: 1.0 nF C0G (CC0603JRNPO9BN102, C106246): Tj stays below 302 F (150 C) in every corner.')
print('Fallback (no schematic change): Nexperia PSMN4R8-100YSE (LFPAK56E, enhanced-SOA ASFET, Tj 175 C, pins 1-3 S / 4 G / mb D = BSC070 TDSON-8 pin map).')

# ---------------- m4: C_BST ----------------
hdr('m4: C_BST 1 uF/50 V 0805 (Pass 3) vs 2.2 uF/50 V 1206 X7R (CL31B225KBHNNNE, C50254). SLUSEW1C 5.3: BST-SRC >= 0.1 uF, no maximum')
src=open(os.path.join(os.path.dirname(__file__),'pass3_calc.py')).read().split('# ================= B1')[0]
exec(src)
C_SLOT=2.7e-6+0.1e-6*(1-0.296)*0.9; C1=2.2e-9; ZH=(15.6+0.6,30.0)
for lab,ceff in (('1 uF 0805 (-16.3 % bias, -10 % tol, -10 % temp, -5 % aging)',1e-6*(1-0.163)*0.9*0.9*0.95),
                 ('2.2 uF 1206 (-30 % bias bound, -10 % tol, -10 % temp, -5 % aging)',2.2e-6*(1-0.30)*0.9*0.9*0.95)):
    N=Net('x',470,C1*1.1,10,True,Rb=1e6,zener=ZH,clamp=True,Cbst=ceff)
    mins=[turn_on_load(N,V0,C_SLOT)[0] for V0 in (12.6,24,28.8,32)]
    print('%s: eff %.3f uF; BST-SRC min %.3f/%.3f/%.3f/%.3f V at 12.6/24/28.8/32 V -> margin to BST_UVLOF max 8.93 V = %.0f mV'%(lab,ceff*1e6,*mins,(min(mins)-8.93)*1e3))
for lab,c in (('1 uF',1e-6*1.1),('2.2 uF',2.2e-6*1.1)):
    print('TDRV_EN %s: C max (+10 %%, no bias loss) x V(BST_UVLOR) max 9.93 V / I(BST) min 190 uA = %.0f ms (typ %.0f ms at 345 uA, 9 V)'%(lab,c*9.93/190e-6*1e3,c/1.1*9.0/345e-6*1e3))
print('-> FW C2.3: after BANK_EN, and after each first slot enable following a bank (re)start, treat BANK_FAULT_N / SLn_PWR_FAULT_N low as "charging" for 150 ms;')
print('   then require high for 10 ms; timeout 250 ms (was 20/10/100 ms).')

# ---------------- m2: R773 ----------------
hdr('m2: R773 BANK_OVL_ROOM pull-down 100k -> 10k against the TCA9555 internal pull-up (IIL <= 100 uA at VI = GND, VCC 1.65-5.5 V)')
Rpu_min=5.5/100e-6
for Vcc in (3.3,3.6):
    for R in (100e3,10e3):
        print('VCC %.1f V, R773 %3.0fk: reset level <= %.3f V (resistive pull-up >= %.0fk); TS5A3166 V_IL max 0.8 V -> %s'%(Vcc,R/1e3,Vcc*R/(R+Rpu_min),Rpu_min/1e3,'LOW (HOT) guaranteed' if Vcc*R/(R+Rpu_min)<0.8 else 'INDETERMINATE'))
print('even if 100 uA flowed at VCC 3.6 V (pull-up 36k): %.3f V < 0.8 V'%(3.6*10e3/(46e3)))
print('driven high: 3.3 V / 10k = %.2f mA (TCA9555 IOH 10 mA per pin); VOH >= 3.1 V > TS5A3166 V_IH 2.4 V; extra %.1f mW while ROOM'%(3.3/10e3*1e3,3.3**2/10e3*1e3))

# ---------------- m9 ----------------
hdr('m9: two channels in current limit at once (3.61 A max each), preloaded at budget (Pass 3 MAJ-A filter, tau min)')
def ttrip(I,I0,Ith,ta): return ta*math.log((I-I0)/(I-Ith))
for m,I0,Ith,tau in (('HOT',2.4,3.15,0.316*0.99*0.9*0.9*(1-0.013)),('ROOM',4.0,5.11,0.195*0.99*0.9*0.9*(1-0.013))):
    t2=ttrip(I0+2*3.61,I0,Ith,tau); t1=ttrip(I0+3.61,I0,Ith,tau)
    print('%s: one channel %.1f ms, two channels %.1f ms -> FW rule ">1 channel faulted at first scan = cut card by 20 ms" keeps %.1f ms margin'%(m,t1*1e3,t2*1e3,(t2-20e-3)*1e3))

# ---------------- m6 / m7 ----------------
hdr('m6 / m7 notes')
print('m6: pass3_calc.txt "Q109 (overload latch)" should read Q108 (AO3400A on BANK_UVLO); Q109 is a slot-1 BSC070N10NS5. Corrected in pass3_calc.py text.')
print('m7: TS5A3166DBVR is -40..185 F (-40..85 C). TS5A3166QDCKRQ1 (AEC-Q100, -40..257 F) exists only in SC-70-5 with 82 in JLC stock; 74LVC1G66-Q100 needs')
print('    V_IH 0.7 x 5 V = 3.5 V (fails from a 3.3 V expander); TMUX1101 is not AEC-Q100 and SOT-23 stock is 0. Keep TS5A3166DBVR + layout keep-away rule.')
