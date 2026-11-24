"""Pass 3 review fixes (docs review modular_pass3: B1, MAJ-A..D, N1..N14). Every number in MODULAR_ARCHITECTURE section 15 and the
Pass 3 rows of FW_REQ_CARDS comes from this script.  Run:  python3 docs/modular/tools/pass3_calc.py > docs/modular/pass3_calc.txt
Sources: TPS48100-Q1 SLUSEW1C; BSC070N10NS5 rev 2.3 (Ciss/Crss/Qg/Qgd, Diagram 3 SOA, output characteristic); INA281-Q1 SBOSA29A;
TLV3012B SBOS300C; TS5A3166 SCDS186E (docs/split_evidence/modular_pass3/pdf); Samsung DC-bias curves (modular_pass3/dcbias.txt);
Samsung class II IR spec (10 G or 500 M*uF initial, 1 G or 50 M*uF after life test); 1N4148W (C81598), BZT52C15 (C2104), TPS1HTC30-Q1.
Temperatures in F (C in parentheses)."""
import math
F=lambda c:c*9/5+32
def hdr(t): print('\n== '+t)
CISS_MAX=2.7e-9; CISS_TYP=2.1e-9; CRSS_MAX=28e-12; QGD_MAX=10e-9; QG_MAX=38e-9; CGS_MIN=CISS_TYP-0.016e-9
def id_fet(vgs,vds,K,Vt):
    vov=max(vgs-Vt,0)
    if vds>=vov: return K*vov*vov
    return K*(2*vov*vds-vds*vds)
def cgd_of(vdg,n): return n*(1.4e-9 if vdg<0 else max(QGD_MAX*0.14/50*(max(vdg,0.05)/50)**(-0.86),CRSS_MAX))
def diode(v,vf0=0.65,rd=6.0): return (v-vf0)/rd if v>vf0 else 0.0
class Net:
    def __init__(s,name,R1,C1,R2,steer,Rb=None,zener=None,clamp=False,Cbst=0.678e-6,n=2):
        s.name,s.R1,s.C1,s.R2,s.steer,s.Rb,s.zener,s.clamp,s.Cbst,s.n=name,R1,C1,R2,steer,Rb,zener,clamp,Cbst,n
    def ic1(s,vg,vc1):
        if s.C1<=0: return 0.0
        return diode(vg-vc1,0.6,s.R2+6.0) if s.steer else (vg-vc1)/s.R2
    def iz(s,vgs):
        if not s.zener: return 0.0
        vz,rz=s.zener; return (vgs-vz)/rz if vgs>vz else 0.0
    def icl(s,vgs,vb): return diode(vgs-vb) if s.clamp else 0.0
def hard_short(N,V0,dV,tf,vb0,drain_fixed,T=12e-6,dt=0.25e-9):
    n=N.n; vs=V0; vgs=vb0; vb=vb0; vc1=V0+vb0-(0.6 if N.steer else 0); pk=vgs; izpk=icpk=0; vbpk=vb
    cgs=n*CGS_MIN
    for i in range(int(T/dt)):
        t=i*dt; vs_new=V0-dV*min(t/tf,1.0); dvs=vs_new-vs; vs=vs_new; vg=vs+vgs
        vdn=V0 if drain_fixed else vs
        i1=(vb-vgs)/N.R1; ic=N.ic1(vg,vc1); iz=N.iz(vgs); icl=N.icl(vgs,vb)
        ib=(vc1-vs)/N.Rb if N.Rb else 0.0
        cgd=cgd_of(vdn-vg,n); dvd=0.0 if drain_fixed else dvs
        vgs+=((i1-ic-iz-icl)*dt+cgd*(dvd-dvs))/(cgs+cgd)
        if N.C1>0: vc1+=(ic-ib)*dt/N.C1
        vb+=(icl-i1)*dt/N.Cbst
        pk=max(pk,vgs); izpk=max(izpk,iz); icpk=max(icpk,icl); vbpk=max(vbpk,vb)
    return pk,izpk,icpk,vbpk
def turn_on_load(N,V0,Cload,vb0=9.27,Ipump=190e-6,K=36.0,Vt=3.82,ciss=CISS_MAX,T=3e-3,dt=4e-9,Ilim_load=None):
    n=N.n; vs=0.0; vgs=0.0; vb=vb0; vc1=0.0; vbmin=vb; ipk=0; t10=t90=None; cgs=n*(ciss-CRSS_MAX)
    for i in range(int(T/dt)):
        vg=vs+vgs
        i1=(vb-vgs)/N.R1; ic=N.ic1(vg,vc1); ib=(vc1-vs)/N.Rb if N.Rb else 0.0; icl=N.icl(vgs,vb)
        idd=n*id_fet(vgs,V0-vs,K,Vt); dvs=idd/Cload*dt
        cgd=cgd_of(V0-vg,n)
        vgs+=((i1-ic-icl)*dt+cgd*(0-dvs))/(cgs+cgd); vs+=dvs
        if N.C1>0: vc1+=(ic-ib)*dt/N.C1
        pump=Ipump if vb<10.37 else 0.0
        vb+=(pump-i1+icl)*dt/N.Cbst
        vbmin=min(vbmin,vb); ipk=max(ipk,idd)
        if t10 is None and vs>0.1*V0: t10=i*dt
        if t90 is None and vs>0.9*V0: t90=i*dt
    return vbmin,vgs,ipk,((t90-t10)*1e6 if (t90 and t10) else None)
def turn_on_short(N,V0,Rpath,vb0=9.27,K=30.0,Vt=2.86,ciss=CISS_MAX,ggood=8.33,ttmr=103e-6,share=1.0,
                  Ccer=34e-6,Cel=200e-6,ESR=50e-3,Rext=30e-3,Lext=1e-6,dt=2e-9,tmax=3e-3):
    """Channel enabled into a dead short (SRC held at 0 V). `share` of the linear-mode current flows in ONE FET (low VGS(th), hot:
    Vt 2.86 V, K 30 A/V2 per FET, both FETs see the same Vgs). VBAT_P stiff-source model: 34 uF ceramics || 200 uF electrolytics
    (50 mOhm ESR) fed by the battery via 30 mOhm + 1 uH. SCP blind until Vgs > G1_GOOD max (8.33 V), then C_TMR timer + tSC."""
    vgs=0.0; vb=vb0; vc1=0.0; vp=V0; vel=V0; ib_=0.0; t=0; E_lin=0; Ppk=0; t_good=None
    cgs=N.n*(ciss-CRSS_MAX); cgd=N.n*CRSS_MAX*1.5
    while True:
        i1=(vb-vgs)/N.R1; ic=N.ic1(vgs,vc1); ibl=vc1/N.Rb if N.Rb else 0
        lo,hi=0.0,vp/Rpath
        for _ in range(40):
            I=(lo+hi)/2; vds=vp-I*Rpath
            if N.n*id_fet(vgs,vds,K,Vt)>I: lo=I
            else: hi=I
        I=(lo+hi)/2; vds=vp-I*Rpath; P=I*vds*share
        if vds>0.2*vp: E_lin+=P*dt; Ppk=max(Ppk,P)
        iel=(vel-vp)/ESR; vel-=iel*dt/Cel; ib_+=(V0-vp-ib_*Rext)/Lext*dt; vp+=(ib_+iel-I)*dt/Ccer
        vgs+=(i1-ic)*dt/(cgs+cgd)
        if N.C1>0: vc1+=(ic-ibl)*dt/N.C1
        vb-=i1*dt/N.Cbst
        if t_good is None and vgs>ggood: t_good=t
        t+=dt
        if (t_good is not None and t>t_good+ttmr+4.3e-6) or t>tmax: break
    teq=E_lin/Ppk if Ppk else 0
    return dict(E_lin=E_lin*1e3,Ppk=Ppk/1e3,teq=teq*1e6,t_good=(t_good or 0)*1e6)
SOA={12.6:{1e-6:320,10e-6:235,100e-6:61},24:{1e-6:320,10e-6:123,100e-6:22.9},32:{1e-6:320,10e-6:100,100e-6:12.8}}   # Diagram 3, Tc 77 F (25 C)
def soa_power(V,tp,derate):
    pts=sorted(SOA[V].items())
    if tp<=pts[0][0]: I=pts[0][1]
    else:
        for (t1,i1),(t2,i2) in zip(pts,pts[1:]):
            if t1<=tp<=t2: I=math.exp(math.log(i1)+(math.log(i2)-math.log(i1))*(math.log(tp)-math.log(t1))/(math.log(t2)-math.log(t1))); break
        else: I=pts[-1][1]*(pts[-1][0]/tp)
    return I*V*derate
DER_149F=(175-65)/(175-25)*0.93    # linear Tj derating 77 F -> 149 F (25 -> 65 C) to Tj max 347 F (175 C), x0.93 margin = 0.68

# ================= B1 / MAJ-C / N11: gate network =================
C_BST_EFF=1e-6*(1-0.163)*0.90*0.90      # 1 uF 50 V 0805 X7R: -16.3 % at 12.83 V (Samsung CL21B105KBFNNNE), -10 % tol, -10 % temp
ZH=(15.6+0.6,30.0)                       # BZT52C15 Vz max 15.6 V + hot tempco 0.6 V, Zzt 30 ohm (C2104)
C1=2.2e-9                                # CC0603KRX7R0BB222 100 V X7R
P2=Net('Pass 2: 150R G1PU, 22 nF + 10R gate->GND, 470 nF C_BST',150,22e-9,10,False,Cbst=0.47e-6*0.8*0.9)
P3=Net('Pass 3: 470R G1PU, gate->1N4148W->10R->2.2 nF->GND (1M C1->SRC), 1N4148W gate->BST, BZT52C15 G-S, 1 uF C_BST',470,C1*1.1,10,True,Rb=1e6,zener=ZH,clamp=True,Cbst=C_BST_EFF)
hdr('B1: peak Vgs when SRC collapses (hard short downstream), channel fully on (BST-SRC at pump max 12.83 V); abs max BST/G1PU/G1PD-SRC 19 V')
print('C_BST effective %.3f uF; C1 modelled at +10 %% (2.42 nF); zener Vz %.1f V / %.0f ohm (worst = highest)'%(C_BST_EFF*1e6,*ZH))
print('drain follows = reviewer model (FET ohmic, Cgd charge ~0); drain fixed = worst bound (full Cgd injection from a stiff drain)')
CASES=((12.6,11.5),(24,22),(28.8,26.5),(32,30))
for N in (P2,P3):
    print(N.name)
    for df in (False,True):
        row=[]
        for V0,dV in CASES:
            for tf in (0.5e-6,1e-6,3e-6):
                pk,iz,icl,vb=hard_short(N,V0,dV,tf,12.83,df); row.append((V0,tf,pk,iz,icl,vb))
        print('   %-13s'%('drain follows' if not df else 'drain fixed')+'  '.join('%.1f V/%.1f us: %.2f'%(r[0],r[1]*1e6,r[2]) for r in row if r[1]!=1e-6))
        print('                 max Vgs %.2f V (limit 17 V), zener peak %.0f mA, BST clamp diode peak %.0f mA, BST-SRC peak %.2f V'%(
              max(r[2] for r in row),max(r[3] for r in row)*1e3,max(r[4] for r in row)*1e3,max(r[5] for r in row)))
hdr('MAJ-C: BST sag at turn-on into the slot load (start at pump-ON min 9.27 V, I_BST min 190 uA, Ciss max, C1 +10 %, C_BST eff)')
C_SLOT=2.7e-6+0.1e-6*(1-0.296)*0.9      # slot card VBAT bulk 2.7 uF + new 100 nF/100 V on SLn_VBAT (-29.6 % at 32 V, -10 %)
print('SLUSEW1C Eq 4: C_BST >= Qg/dV_BST + 10*C1 = 2*38 nC/(9.27-8.93 V) + 10*%.2f nF = %.0f nF; fitted %.0f nF effective (%.1fx)'%(
      C1*1.1e9,(76e-9/0.34+10*C1*1.1)*1e9,C_BST_EFF*1e9,C_BST_EFF/(76e-9/0.34+10*C1*1.1)))
Pslow=Net('slow',470,C1*1.1,10,True,Rb=1e6,zener=ZH,clamp=True,Cbst=C_BST_EFF)
for V0 in (12.6,24,28.8,32):
    vbmin,vg,ipk,ramp=turn_on_load(Pslow,V0,C_SLOT)
    print('%4.1f V: BST-SRC min %.3f V (> BST_UVLOF max 8.93 V by %.3f V; > G1_GOOD max 8.33 V), final Vgs %.2f V, inrush %.1f A, 10-90 %% %.1f us'%(V0,vbmin,vbmin-8.93,vg,ipk,ramp))
print('Pass 2 network for reference:')
for V0 in (12.6,32):
    vbmin,vg,ipk,ramp=turn_on_load(P2,V0,C_SLOT); print('   %4.1f V: BST-SRC min %.3f V'%(V0,vbmin))
hdr('Inrush, fast corner (C1 -10 % tol -30 % bias, C_BST 1.1 uF at 12.83 V, low-Vth hot FET, Ciss typ)')
Pfast=Net('fast',470,C1*0.9*0.7,10,True,Rb=1e6,zener=ZH,clamp=True,Cbst=1.1e-6)
for V0 in (12.6,32):
    vbmin,vg,ipk,ramp=turn_on_load(Pfast,V0,C_SLOT,vb0=12.83,K=30,Vt=2.86,ciss=CISS_TYP)
    print('%4.1f V: inrush peak %.1f A for %.1f us (slot SCP blind below G1_GOOD; bank SCP min 21.2 A timer needs 517 us -> no trip)'%(V0,ipk,ramp))
print('Eq 3 typ: I_inrush = 0.63*11 V*%.2f uF/(470*2.2 nF) = %.1f A'%(C_SLOT*1e6,0.63*11*C_SLOT/(470*C1)))
hdr('N11: turn-on into a dead short at 32 V, Tc 149 F (65 C), one FET takes the bulk of the linear-mode current')
print('SOA derating at Tc 149 F (65 C) = %.2f'%DER_149F)
for lab,ttmr,Rp in (('slot (C_TMR 4.7 nF, 103 us max)',103e-6,27e-3),('bank (C_TMR 68 nF, 1490 us max)',1490e-6,27e-3)):
    for share in (1.0,0.75):
        s=turn_on_short(Pfast if False else P3,32,Rp,share=share,ttmr=ttmr)
        soa=soa_power(32,max(s['teq']*1e-6,1e-7),DER_149F)/1e3
        print('%s, %3.0f %% in one FET: linear-mode energy %.1f mJ, Ppk %.2f kW, t_eq %.2f us, derated SOA %.2f kW -> ratio %.2f'%(lab,share*100,s['E_lin'],s['Ppk'],s['teq'],soa,s['Ppk']/soa))
for nm,N in (('Pass 2 150R/22n',P2),('TI 100k/220p',Net('TI',100e3,220e-12,10,False,Cbst=C_BST_EFF))):
    s=turn_on_short(N,32,27e-3,share=1.0); soa=soa_power(32,max(s['teq']*1e-6,1e-7),DER_149F)/1e3
    print('%s for comparison: E_lin %.0f mJ, Ppk %.2f kW, t_eq %.1f us, ratio %.2f'%(nm,s['E_lin'],s['Ppk'],s['teq'],s['Ppk']/soa))
print('-> the turn-on-into-short peak is set by the stiff VBAT_P source, not the gate network: firmware must not auto-retry a slot that'
      ' latched SCP (C7.9), and the first power-on of a new card is a bench test item (MOD section 15.4).')

# ================= N1: SCP grading =================
hdr('N1: TPS48100 SCP thresholds, offset-correct model V_SCP = 19 mV + (V_28k - 19 mV)*R/28k, shunt +/-1 %')
ROW28=(58.8e-3,75e-3,91.8e-3)
def scp(R,rs=5e-3):
    v=[19e-3+(x-19e-3)*R/28e3 for x in ROW28]; return v[0]/rs*0.99,v[1]/rs,v[2]/rs*1.01
def tmr(C,R=100e3):
    def t(c,i,v): return R*c*math.log(1/(1-v/(R*i)))
    return t(C*0.9,114e-6,0.924),t(C,87e-6,1.1),t(C*1.1,67e-6,1.21)
slot=scp(24.3e3); bank=scp(61.9e3); ts=tmr(4.7e-9); tb=tmr(68e-9)
print('slot 24.3k: %.1f/%.1f/%.1f A, latch-off %.0f/%.0f/%.0f us'%(*slot,*(x*1e6 for x in ts)))
print('bank 61.9k: %.1f/%.1f/%.1f A, latch-off %.0f/%.0f/%.0f us  (time grading bank min / slot max = %.2fx)'%(*bank,*(x*1e6 for x in tb),tb[0]/ts[2]))
for m,b in (('HOT',2.4),('ROOM',4.0)):
    print('current grading %s: bank SCP min %.2f A > slot SCP max %.2f A + %.1f A budget = %.2f A (margin %+.2f A)'%(m,bank[0],slot[2],b,slot[2]+b,bank[0]-slot[2]-b))
print('68.1k alternative: %.1f/%.1f/%.1f A (raises the double-fault I2t, not taken)'%scp(68.1e3))

# ================= MAJ-A: bank overload cutoff =================
hdr('MAJ-A: INA281A2 -> 15.8k / 2x10 uF (HOT) or 15.8k||25.5k via TS5A3166 (ROOM) -> TLV3012B (V_TH 0.8613 V)')
G=50; RS=5e-3; VREF=1.242; RA,RB=44.2e3,100e3; R1F=15.8e3; RX=25.5e3; CF=20e-6; ISAT=(4.9-0.15)/(G*RS)
VTH=VREF*RB/(RA+RB)
TMIN=0.99*0.90*0.90*(1-0.013); TMAX=1.01*1.10      # R 1 %; C -10 % tol, -10 % at 185 F (85 C), -1.3 % DC bias at 1.5 V; C +10 % max
print('tau factors: min %.3f (R -1 %%, C -10 %% tol, -10 %% hot, -1.3 %% bias), max %.3f'%(TMIN,TMAX))
win={}
for m,room in (('HOT',False),('ROOM',True)):
    k=RX/(R1F+RX) if room else 1.0; I=VTH/(G*RS*k); vsh=I*RS; Rth=(R1F*RX/(R1F+RX)) if room else R1F; tau=Rth*CF
    e=dict(ref=1.5+100e-6*40*100,div=2*1.0*RA/(RA+RB),cmp_vos=9e-3/VTH*100,cmp_hys=8e-3/VTH*100,ina_gain=0.5+20e-6*40*100,
           ina_vos=(300e-6+1e-6*40)/vsh*100,shunt=1.0+75e-6*40*100,filt=(2*1.0*R1F/(R1F+RX)) if room else 0)
    tot=sum(e.values())
    sw=100e-9*Rth/VTH*100      # TS5A3166 NO off-leakage +/-100 nA max (-40..185 F) into the filter node
    ir=tau/50.0*100            # MLCC IR floor 50 M*uF (life-test spec; stands in for 185 F) -> node loss R/IR = tau/50 s
    lo=I*(1-tot/100-sw/100); hi=I*(1+tot/100)*(1+sw/100+ir/100)
    win[m]=(I,lo,hi,tau)
    print('%s: k %.4f, tau %.0f ms, trip nominal %.2f A, window %.2f..%.2f A (tolerances +/-%.2f %%, switch leakage %.2f %%, cap IR +%.2f %%)'%(m,k,tau*1e3,I,lo,hi,tot,sw,ir))
print('   Pass 2 for reference: AO3400A IDSS bound 1 uA (77 F) into the 220k node = %.0f %% of V_TH, 5 uA at 131 F (55 C) worse: not budgetable (review MAJ-A)'%(1e-6*220e3/VTH*100))
print('   Pass 3: TS5A3166 +/-100 nA max over -40..185 F (-40..85 C) into 15.8k = %.2f %% of V_TH (< 0.25 %%)'%(100e-9*R1F/VTH*100))
print('INA281 output saturates at %.1f A'%ISAT)
def ttrip(I,I0,Ith,ta):
    Ie=min(I,ISAT)
    if Ie<=Ith: return math.inf
    return ta*math.log((Ie-min(I0,Ith))/(Ie-Ith))
CH=3.61; BUD={'HOT':2.4,'ROOM':4.0}; FWISO=25e-3
for m in ('HOT','ROOM'):
    I,lo,hi,tau=win[m]; b=BUD[m]
    print('%s budget %.1f A (margin to trip min %.2f A):'%(m,b,lo-b))
    tmn=ttrip(b+CH,0,lo,tau*TMIN)
    print('   from cold, budget + one channel in current limit (3.61 A max) = %.2f A: trips no sooner than %.1f ms'%(b+CH,tmn*1e3))
    for I0 in (1.0,2.0,b):
        tmn=ttrip(I0+CH,I0,lo,tau*TMIN)
        s='never trips' if tmn==math.inf else 'trips no sooner than %.1f ms (FW isolation <= %.0f ms -> %.1fx)'%(tmn*1e3,FWISO*1e3,tmn/FWISO)
        print('   preloaded at %.1f A for > 5 tau, then one channel in current limit: bank %.2f A %s'%(I0,I0+CH,s))
    for Ix in (6,8,10.6,16.6,ISAT):
        print('   %5.1f A from cold: %.0f..%.0f ms'%(Ix,ttrip(Ix,0,lo,tau*TMIN)*1e3,ttrip(Ix,0,hi,tau*TMAX)*1e3))
    print('   re-arm: filter back to < 1 %% after 5 tau max = %.2f s (FW waits >= 3 s)'%(5*tau*TMAX))
hdr('F1 10 A ATO coordination (hold 110 %; hot rerate 0.8 at 149 F; melt I2t 115 A2s room, ~74 A2s hot [estimate])')
for m,amb,base,hold,melt in (('ROOM',25,59.4/12.4,11.0,115.0),('HOT',65,4.95,8.8,74.0)):
    I,lo,hi,tau=win[m]; b=BUD[m]
    print('%s (%.0f F): base %.2f A + trip max %.2f A = %.2f A vs F1 hold %.1f A (margin %.2f A)'%(m,F(amb),base,hi,base+hi,hold,hold-base-hi))
    Is=slot[2]+b; tsg=ttrip(Is,0,hi,tau*TMAX); i2s=(min(Is,40)+base)**2*tsg
    tdb=ttrip(bank[0],0,hi,tau*TMAX); i2d=(bank[0]+base)**2*tdb
    print('   single fault: slot at SCP max %.1f A + %.1f A budget, unpreloaded: bank trips <= %.0f ms, F1 %.1f A -> %.1f A2s (%.0f %% of %.0f)'%(slot[2],b,tsg*1e3,Is+base,i2s,i2s/melt*100,melt))
    print('   double fault just under bank SCP min %.1f A: <= %.0f ms, %.1f A2s (%.0f %%)'%(bank[0],tdb*1e3,i2d,i2d/melt*100))
print('ROOM VBAT floor 12.4 V: firmware leaves ROOM (selects HOT) below 12.4 V; base 59.4 W / 12.4 V = %.2f A'%(59.4/12.4))
print('multi-fault above bank SCP min (> %.1f A): bank SCP latches in 517-1490 us; a hard short on VBAT_SLOTS copper may still open F1 (board-fault class, Pass 2)'%bank[0])
hdr('Bank FET / shunt steady state at the trip max (RthJA 50 K/W, RDS(on) 7 mOhm x 1.5 hot, 60/40 split)')
for m,amb in (('ROOM',25),('HOT',65)):
    I=win[m][2]; p=(0.6*I)**2*7e-3*1.5; print('%s %.0f F, %.2f A: hot FET %.2f W, Tj %.0f F; shunt %.2f W of 3 W'%(m,F(amb),I,p,F(amb+50*p),I*I*RS))

# ================= MAJ-B: UVLO RC =================
hdr('MAJ-B: 4.7 nF on BANK_UVLO and SL1-8_UVLO (100k/27k divider, Thevenin 21.26k)')
Rth=100e3*27e3/127e3
for lab,c in (('min',4.7e-9*0.9*0.9),('typ',4.7e-9),('max',4.7e-9*1.1)):
    print('tau %s %.0f us'%(lab,Rth*c*1e6))
tau_min=Rth*4.7e-9*0.81
for V0 in (12.6,24,32):
    for Vd in (4.0,6.0):
        v0=V0*27/127; vinf=Vd*27/127
        if vinf>=1.083: print('VS %.1f V dips to %.1f V: node settles at %.2f V >= UVLOF min 1.083 V -> no UVLO turn-off'%(V0,Vd,vinf)); continue
        t=tau_min*math.log((v0-vinf)/(1.19-vinf))+2.8e-6
        print('VS %.1f V dips to %.1f V: UVLO node %.2f V -> UVLOF max 1.19 V after >= %.0f us (> slot SCP latch-off max 103 us)'%(V0,Vd,v0,t*1e6))
print('turn-on delay added: <= 5 tau max = %.2f ms; Q108 (overload latch; Pass 4 m6: was misprinted Q109) discharges the cap through AO3400A in < 1 us'%(5*Rth*4.7e-9*1.1*1e3))
print('Bulk would not help: holding VBAT_SLOTS above 4 V through a 300 A, 100 us short needs C >= 300 A*100 us/8.6 V = %.1f mF'%(300*100e-6/8.6*1e3))

# ================= MAJ-D: VS/SRC caps =================
hdr('MAJ-D: 100 nF / 100 V 0805 X7R (CL21B104KCFNNNE) on VBAT_SLOTS (U110 SRC + 8 slot VS) and on each SLn_VBAT')
for V,dc in ((12.6,-7.6),(24,-19.9),(32,-29.6),(36,-34.6)):
    print('%4.1f V: %.1f nF typ, %.1f nF worst (-10 %% tol)  >= 22 nF'%(V,100*(1+dc/100),100*(1+dc/100)*0.9))
print('slot load cap at turn-on with the new 100 nF: %.2f uF (inrush above)'%(C_SLOT*1e6))
print('bank turn-on into VBAT_SLOTS (9 x 100 nF): typ dV/dt 0.63*11/(470*2.2n)=%.1f V/us -> %.1f A'%(0.63*11/(470*2.2e-9)*1e-6,0.63*11/(470*2.2e-9)*9*0.1e-6*0.7))
