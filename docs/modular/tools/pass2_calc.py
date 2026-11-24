"""Pass 2 review fixes: every number quoted in MODULAR_ARCHITECTURE §14 / FW_REQ_CARDS comes from here.
Sources (docs/split_evidence/modular_pass1 + modular_pass2): TPS48100-Q1 SLUSEW1C, INA281-Q1 SBOSA29A, TLV3012B SBOS300C,
74LVC1G74-Q100 (Nexperia rev 6), BSC070N10NS5 rev 2.3, IRLML0100 (PD-97157), AT24CS32 DS20005767, TPS2553 SLVS841G.
Run: python3 docs/modular/tools/pass2_calc.py > docs/modular/pass2_calc.txt"""
import math
F=lambda c:c*9/5+32
def hdr(t): print('\n== '+t)
# ---------------- TPS48100 SCP threshold (Eq 5) and fault timer (Eq 9, 100k latch) ----------------
LO,HI=0.784,1.224          # min/typ, max/typ from the 28k row (58.8/75/91.8 mV); 10.5k row is 0.79/1.2375
def scp(R,rs=5e-3):
    v=19e-3+2e-6*R; return v*LO/rs,v/rs,v*HI/rs,v
def tmr(C,R=100e3):
    def t(c,i,v): return R*c*math.log(1/(1-v/(R*i)))
    return t(C*0.9,114e-6,0.924),t(C,87e-6,1.1),t(C*1.1,67e-6,1.21)
hdr('TPS48100 thresholds (A) and latch-off timers (us)')
slot=scp(24.3e3); bank=scp(61.9e3)
print('slot 24.3k: %.1f/%.1f/%.1f A  V_SCP typ %.1f mV'%(slot[0],slot[1],slot[2],slot[3]*1e3))
print('bank 61.9k: %.1f/%.1f/%.1f A  V_SCP typ %.1f mV'%(bank[0],bank[1],bank[2],bank[3]*1e3))
ts=tmr(4.7e-9); tb=tmr(68e-9)
print('slot 4.7 nF: %.0f/%.0f/%.0f us'%tuple(x*1e6 for x in ts))
print('bank 68 nF : %.0f/%.0f/%.0f us  (bank min / slot max = %.1fx)'%(*(x*1e6 for x in tb),tb[0]/ts[2]))
print('latch clamp R*I_TMR_SRC_FLT max = 100k*4.8uA = %.2f V < V_TMR_SC min 0.924 V'%(100e3*4.8e-6))
print('current grading: bank SCP min %.1f A vs slot SCP max %.1f A + 5.0 A other slots = %.1f A'%(bank[0],slot[2],slot[2]+5))
# ---------------- bank SCP energy, FET SOA ----------------
hdr('Bank SCP stress, both FETs fully on (RDS(on) 7 mOhm max at 25 C, x1.5 hot)')
for I in (bank[2],):
    t=tb[2]; p_fet=(I*0.6)**2*7e-3*1.5; p_sh=I**2*5e-3
    print('I=%.1f A for %.2f ms: hot FET (60/40) %.1f W, shunt %.1f W (%.0f mJ; 3 W 2512 short-time OK), FET in RDS(on), not SOA-limited'%(I,t*1e3,p_fet,p_sh,p_sh*t*1e3))
print('hard short on VBAT_SLOTS copper: ~230 A for 1.49 ms max = %.0f A2s -> F1 (115 A2s melt) may open: board-fault class, same as a VBAT_P short'%(230**2*tb[2]))
# ---------------- bank hardware overload timer ----------------
hdr('Bank overload cutoff: INA281A2 (50 V/V) on the 5 mOhm bank shunt -> RC -> TLV3012B -> 74LVC1G74 latch -> BANK_UVLO low')
G=50; RS=5e-3; R1=220e3; RX=365e3; CF=1e-6; RA,RB=44.2e3,100e3
VREF=1.242; VTH=VREF*RB/(RA+RB)
modes={'HOT (Rx off, default)':1.0,'ROOM (Rx on, firmware selects only while F1 state = ROOM, <= 77 F)':RX/(R1+RX)}
tau={'HOT (Rx off, default)':R1*CF,'ROOM (Rx on, firmware selects only while F1 state = ROOM, <= 77 F)':(R1*RX/(R1+RX))*CF}
print('V_TH = 1.242 V x 100k/144.2k = %.4f V'%VTH)
res={}
for m,k in modes.items():
    I=VTH/(G*RS*k); vsh=I*RS
    e=dict(ref=1.5+100e-6*40*100, div=2*1.0*RA/(RA+RB), cmp_vos=9e-3/VTH*100, cmp_hys=8e-3/VTH*100,
           ina_gain=0.5+20e-6*40*100, ina_vos=(300e-6+1e-6*40)/vsh*100, shunt=1.0+75e-6*40*100,
           filt=(2*1.0*R1/(R1+RX)) if k<1 else 0)
    tot=sum(e.values()); res[m]=(I,I*(1-tot/100),I*(1+tot/100))
    print('%s: k=%.4f  tau=%.0f ms  trip nominal %.2f A, worst-case +/-%.1f%% -> %.2f..%.2f A'%(m,k,tau[m]*1e3,I,tot,res[m][1],res[m][2]))
    print('   error terms %%: '+', '.join('%s %.2f'%(a,b) for a,b in e.items()))
ISAT=(4.9-0.15)/(G*RS)
print('INA281 output saturates at (+5V_TRIP min 4.9 V - 0.15 V)/0.25 V/A = %.1f A'%ISAT)
def ttrip(I,Ith,ta): Ie=min(I,ISAT); return math.inf if Ie<=Ith else ta*math.log(Ie/(Ie-Ith))
CH=3.61   # one shorted TPS1HTC30 channel at its max limit
for m,budget in (('HOT (Rx off, default)',3.0),('ROOM (Rx on, firmware selects only while F1 state = ROOM, <= 77 F)',5.0)):
    I,lo,hi=res[m]; ta=tau[m]
    print(m)
    print('   budget %.1f A: never trips (min threshold %.2f A)'%(budget,lo))
    print('   budget + one shorted channel %.2f A: trips no sooner than %.0f ms (tau-20%%, Ith min); firmware channel latch <= 80 ms'%(budget+CH,ttrip(budget+CH,lo,ta*0.8)*1e3))
    for Ix in (8,10.7,16.6,ISAT):
        print('   %5.1f A: %.0f..%.0f ms'%(Ix,ttrip(Ix,lo,ta*0.8)*1e3,ttrip(Ix,hi,ta*1.15)*1e3))
# ---------------- F1 ladder ----------------
hdr('F1 10 A ATO coordination (base load 4.95 A at 12 V, 6.46 A at 9 V; F1 hold 110% >= 100 h; hot rerate 0.8)')
for amb,frat,m in ((25,10.0,'ROOM (Rx on, firmware selects only while F1 state = ROOM, <= 77 F)'),(65,8.0,'HOT (Rx off, default)')):
    hold=1.1*frat; I,lo,hi=res[m]
    print('%.0f F: F1 holds %.1f A; base 4.95 + bank overload max %.2f = %.2f A (margin %.2f A)'%(F(amb),hold,hi,4.95+hi,hold-4.95-hi))
    tw=ttrip(slot[2]+5.0,hi,tau[m]*1.15); Iw=min(slot[2]+5.0,40)+4.95
    print('   worst single fault (slot at SCP max %.1f + 5 A others): bank trips <= %.0f ms; F1 sees %.1f A -> %.0f A2s (melt I2t 115 room, ~74 hot [E])'%(slot[2],tw*1e3,Iw,Iw**2*tw))
    tw2=ttrip(bank[0],hi,tau[m]*1.15); Iw2=bank[0]+4.95
    print('   double fault just under bank SCP min %.1f A: <= %.0f ms, %.0f A2s'%(bank[0],tw2*1e3,Iw2**2*tw2))
# ---------------- bank FET thermal at the overload threshold ----------------
hdr('Bank FET / shunt steady state at the overload threshold (RthJA 50 K/W, RDS(on) 7 mOhm x 1.5 hot, 60/40 split)')
for amb,m in ((25,'ROOM (Rx on, firmware selects only while F1 state = ROOM, <= 77 F)'),(65,'HOT (Rx off, default)')):
    I=res[m][2]; p=(0.6*I)**2*7e-3*1.5; tj=amb+50*p
    print('%.0f F, %.2f A: hot FET %.2f W, Tj %.0f F; shunt %.2f W of 3 W'%(F(amb),I,p,F(tj),I*I*RS))
# ---------------- slot / bank gate dV/dt (SLUSEW1C Fig 7-4, Eq 3/4) ----------------
hdr('Gate dV/dt: R1 150R G1PU->gate, C1 22 nF + R2 10R gate->GND (slot and bank)')
R1g=150; C1=22e-9; Vdrv=11-4.8   # V(BST-SRC) 11 V minus the 4.8 V Miller plateau
sr=Vdrv/(R1g*C1); Cl=2.7e-6
print('output slew %.2f V/us; 32 V in %.0f us; inrush into 2.7 uF card bulk %.1f A (slot SCP min %.1f A)'%(sr/1e6,32/sr*1e6,Cl*sr,slot[0]))
tlin=1.19*R1g*(C1+2.7e-9*2)
print('turn-on into a short: linear window ~%.1f us; SOA 10 us line ~94 A at 32 V (Tc 77 F), x0.68 at 149 F = ~2 kW: inside'%(tlin*1e6))
print('CBST >= Qg/dV + 10*C1 = 2x38 nC/1 V + 220 nF = %.0f nF; fitted 470 nF'%((76e-9/1+10*C1)*1e9))
# ---------------- MAJ-3 bleeder ----------------
hdr('VBAT_ESTOP switched bleeder: 2x 2.2k 2512 1 W (1.1k) + IRLML0100, on when RC_EN low')
Rb=1/(1/1100+1/40.3e3)+0.235; Cb=1.85e-6
for c in (Cb,Cb*1.2):
    t=Rb*c; print('C=%.2f uF tau=%.2f ms: '%(c*1e6,t*1e3)+', '.join('%.1f V->2 V %.2f ms'%(v,t*math.log(v/2)*1e3) for v in (12.6,24,28.8,32)))
for v in (32,36):
    print('stuck-on Q101/Q102 at %d V: %.2f W total, %.2f W per 1 W 2512 (%.0f%%)'%(v,v*v/1100,v*v/2200,v*v/2200*100))
print('IRLML0100 gate 5 V (+5V_TRIP via 100k) vs VGS(th) 2.5 V max; RDS(on) <= 235 mOhm at 4.5 V; ID <= %.0f mA'%(36/1100*1e3))
# ---------------- m1 ANA settling ----------------
hdr('SLOT_ANA settling with 1k series per slot')
Rsrc=4.7e3+910+7+1e3+7; Ca=10e-9
for c in (Ca,Ca*1.1):
    print('C224 %.0f nF: tau %.1f us, 12-bit (ln 8192 = 9.01 tau) %.2f ms'%(c*1e9,Rsrc*c*1e6,9.01*Rsrc*c*1e3))
print('firmware wait 0.8 ms; unpowered-slot dump through 1k <= %.1f mA (TMUX1208 S abs max 30 mA)'%(3.3/1e3*1e3))
# ---------------- m14 +3V3_ID ----------------
hdr('+3V3_ID feed 68R 1206 0.25 W')
I=3.0e-3+0.33e-3+0.33e-3
print('short: %.0f mW (%.0f%% of 250 mW); load %.2f mA (AT24CS32 ICC2 write 3 mA max @5 V + 2x 10k) -> droop %.0f mV -> +3V3_ID >= %.2f V (3.25 V SAFE min)'%(3.3**2/68*1e3,3.3**2/68/0.25*100,I*1e3,I*68*1e3,3.25-I*68))
print('SDA pulled to +3V3_SAFE 3.3 V; VIH max = VCC + 0.5 = %.2f V -> margin %.0f mV (150R: VCC %.2f V, margin %.0f mV)'%(3.25-I*68+0.5,(3.25-I*68+0.5-3.3)*1e3,3.25-I*150,(3.25-I*150+0.5-3.3)*1e3))
# ---------------- m9 AI-4 back-power ----------------
hdr('AI-4 back-power: IN -> R9 100k -> BAV99 -> +3V3_SLOT (TPS2553 has no QOD; only TPS25530-1 does)')
for Rbl in (None,1e3,2.2e3,4.7e3):
    i=4*(24-0.6)/100e3
    print('bleeder %s: 4 inputs at 24 V inject %.2f mA -> rail %s'%('none' if Rbl is None else '%.1fk'%(Rbl/1e3),i*1e3,'set by IC leakage (>1.65 V possible)' if Rbl is None else ('%.2f V, %.0f mW at 3.3 V'%(i*Rbl,3.3**2/Rbl*1e3) if i*Rbl<1.65 else 'not clamped (I*R = %.2f V > 1.65 V, rail sits near the input clamp level)'%(i*Rbl))))
# ---------------- m12 DIN contact sharing ----------------
hdr('DIN C96 VBAT_FIELD sharing: 9 contacts, 2 A each, 20 mOhm max; worst split one 5 mOhm vs eight 20 mOhm = 1/3')
for lab,I in (('5.0 A budget',5.0),('room overload max %.2f A'%res['ROOM (Rx on, firmware selects only while F1 state = ROOM, <= 77 F)'][2],res['ROOM (Rx on, firmware selects only while F1 state = ROOM, <= 77 F)'][2]),('even split 5 A',5.0*3/9)):
    print('%s: worst contact %.2f A'%(lab,I/3 if 'even' not in lab else 5/9))
print('slot short above SCP (max %.1f A) for <= 103 us: worst contact %.1f A (I2t %.4f A2s)'%(slot[2],slot[2]/3,(slot[2]/3)**2*103e-6))
print('slot overload just below slot SCP min %.1f A: worst contact %.1f A until the bank overload trips (<= %.0f ms HOT, <= %.0f ms ROOM) unless firmware drops the slot in 50 ms'%(slot[0],slot[0]/3,ttrip(slot[0],res['HOT (Rx off, default)'][2],tau['HOT (Rx off, default)']*1.15)*1e3,ttrip(slot[0],res['ROOM (Rx on, firmware selects only while F1 state = ROOM, <= 77 F)'][2],tau['ROOM (Rx on, firmware selects only while F1 state = ROOM, <= 77 F)']*1.15)*1e3))
