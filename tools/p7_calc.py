#!/usr/bin/env python3
"""m7-split P7 (2026-11-24 HST): Q2 BSC070N10NS5 start-up with the front-end fix ported from m7-modular (MOD sections 19/20 + Pass 8):
R1001 1k + C601 22 nF HGATE dV/dt, C602 1 uF on U2 EN/UVLO, U5 EN divider R1125 100k / R1126 47k, Vds hold-off D401/Q121/R1121-R1124/
C1121/Q122/D402. Model, SOA curve and hold-off corners copied verbatim from m7-modular docs/modular/tools/pass6_fix_calc.py and
kick_calc.py (soa_i/soa_check); only the VBAT_P capacitance differs (split: + 15 x 100 nF TPS1HTC30 VS caps + C225 10 uF behind D120).
Also checks the drawn part values in power.kicad_sch (m7-modular Pass 8 found R1121/R1123 = 2.2k, R1126 = 4.7k there)."""
import os,re,sys,math
import numpy as np
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F=lambda c:c*9/5+32
CC=4*10e-6*0.65+2.2e-6*0.6+0.2e-6+2*100e-6 + 15*100e-9*0.8 + 10e-6*0.5     # ~234 uF effective
print(__doc__)
# ---- 0. drawn values (fails loudly if a part is wrong)
s=open(os.path.join(ROOT,'power.kicad_sch')).read()
# C601: 100 nF C15725 since the SPICE pass (docs/spice/README.md); the hand-calc model below keeps the P7 22 nF record.
WANT={'R1001':('1k','C21190'),'C601':('100n 100V','C15725'),'C602':('1u 50V','C28323'),'D401':('1N4148W','C81598'),'Q121':('MMBT5401','C8326'),
      'R1121':('22k','C31850'),'R1122':('68k','C23231'),'R1123':('22k','C31850'),'R1124':('100k','C25803'),'C1121':('100n','C14663'),
      'Q122':('MMBT3904','C20526'),'D402':('BAT54C','C37704'),'R1125':('100k','C25803'),'R1126':('47k','C25819'),'R4':('100k',None),'R5':('33k',None)}
bad=0
for ref,(val,lc) in WANT.items():
    m=re.search(r'\(property "Reference" "%s".*?\(property "Value" "([^"]*)".*?(?:\(property "LCSC" "([^"]*)")?'%ref,s,re.S)
    blk=s[m.start():m.start()+3000] if m else ''
    v=m.group(1) if m else None; l=re.search(r'\(property "LCSC" "([^"]*)"',blk); l=l.group(1) if l else None
    ok=(v==val) and (lc is None or l==lc); bad+=not ok
    print('  %-6s %-9s %-8s %s'%(ref,v,l,'OK' if ok else 'WRONG (want %s %s)'%(val,lc)))
if bad: sys.exit('drawn values wrong: %d'%bad)
# outputs.kicad_sch: G1PU slew and TMR latch-off (SPICE follow-up, 2026-11-24)
so=open(os.path.join(ROOT,'outputs.kicad_sch')).read()
WANT_OUT={'R295':('22k','C31850'),'R301':('22k','C31850'),'R650':('100k','C25803'),'R651':('100k','C25803')}
for ref,(val,lc) in WANT_OUT.items():
    m=re.search(r'\(property "Reference" "%s".*?\(property "Value" "([^"]*)"'%ref,so,re.S)
    blk=so[m.start():m.start()+3000] if m else ''
    v=m.group(1) if m else None; l=re.search(r'\(property "LCSC" "([^"]*)"',blk); l=l.group(1) if l else None
    ok=(v==val) and (l==lc); bad+=not ok
    print('  %-6s %-9s %-8s %s'%(ref,v,l,'OK' if ok else 'WRONG (want %s %s)'%(val,lc)))
for ref in ('C197','C201'):
    m=re.search(r'\(symbol \(lib_id "Device:C"\)[^)]*\(dnp (yes|no)\)[^)]*\n\(property "Reference" "%s"'%ref,so)
    # fallback: search the symbol that contains this Reference
    if not m:
        i=so.find('(property "Reference" "%s"'%ref)
        head=so[max(0,i-400):i]
        dnp='yes' if '(dnp yes)' in head else ('no' if '(dnp no)' in head else None)
    else:
        dnp=m.group(1)
    ok=dnp=='yes'; bad+=not ok
    print('  %-6s dnp=%-5s           %s'%(ref,dnp,'OK' if ok else 'WRONG (want DNP)'))
if bad: sys.exit('drawn values wrong: %d'%bad)

SOA_100US=[(10,74.8),(20,31.5),(40,7.77),(90,1.54)]
SOA_A={1e-3:1160.0,1e-2:359.0,1.0:167.0}
def soa_i(V,tau):
    V=max(V,1.0)
    def l100(V):
        pts=SOA_100US
        if V<=pts[0][0]: return pts[0][1]*(pts[0][0]/V)
        for (v1,i1),(v2,i2) in zip(pts,pts[1:]):
            if v1<=V<=v2: return math.exp(math.log(i1)+(math.log(i2)-math.log(i1))*(math.log(V)-math.log(v1))/(math.log(v2)-math.log(v1)))
        return pts[-1][1]*(pts[-1][0]/V)**2
    lines=[(1e-4,l100(V))]+[(t,A/V/V) for t,A in sorted(SOA_A.items())]
    if tau<=lines[0][0]: return lines[0][1]
    for (t1,i1),(t2,i2) in zip(lines,lines[1:]):
        if t1<=tau<=t2: return math.exp(math.log(i1)+(math.log(i2)-math.log(i1))*(math.log(tau)-math.log(t1))/(math.log(t2)-math.log(t1)))
    return lines[-1][1]
def soa_check(vds,iD,Tc=65.0,dt=1e-5):
    """Worst sliding-window ratio I_avg / (SOA(V_eff, tau) x (150-Tc)/125) for tau = 0.1/1/10 ms and the whole event;
    V_eff = P_avg / I_avg. Returns (ratio, tau, V_eff, I_avg)."""
    der=(150.0-Tc)/125.0; best=(0.0,0,0,0); n=len(vds)
    if n==0: return best
    P=np.concatenate([[0.0],np.cumsum(vds*iD)]); I=np.concatenate([[0.0],np.cumsum(iD)])
    for tau in (1e-4,1e-3,1e-2,n*dt):
        w=max(1,min(n,int(round(tau/dt))))
        Ia=(I[w:]-I[:-w])/w if w<n else np.array([I[-1]/n]); Pa=(P[w:]-P[:-w])/w if w<n else np.array([P[-1]/n])
        for k in np.argsort(-Pa)[:200]:
            if Ia[k]<=1e-3: continue
            Ve=Pa[k]/Ia[k]; r=Ia[k]/(soa_i(Ve,w*dt)*der)
            if r>best[0]: best=(r,w*dt,Ve,Ia[k])
    return best



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
    Cc=CC
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
    sc=soa_check(np.array(trv),np.array(tri))
    return dict(E=E,t=t,soa=sc[0],tau=sc[1],t_eng=t_eng,t_u2off=t_u2off,t_u2on=t_u2on,u2=u2)


def ms(x): return '   -  ' if x is None else '%6.2f'%(x*1e3)
print('\nVBAT_P effective capacitance %.0f uF (m7-modular 228 uF)'%(CC*1e6))
print('\n== 1. Hold-off threshold vs temperature (Vth = Vf(D401) + Veb(Q121) x 90k/22k)')
for c in (COLD,NOM,HOT): print('  %-20s Vf %.2f V, Veb %.2f V -> Vth %.2f V'%(c[0],c[1],c[2],vth(c)))
print('\n== 2. U5 EN divider 100k / 47k: on at VBAT_P %.2f-%.2f V, EN at 57.6 V clamp = %.1f V (abs max VIN+0.3)'%(1.16*147/47,1.36*147/47,57.6*47/147))
print('\n== 3. Q2 cold start (U2 70 W and U5 2.1 W held off until BAT_IN - VBAT_P < Vth; C602 from 0 V)')
worst=0
for Vb in (12.0,13.8,24.0,28.8,32.0):
    for ihg in (39e-6,75e-6):
        for c in (COLD,HOT):
            r=run(Vb,ihg,c); worst=max(worst,r['soa'])
            print('  %4.1f V %2.0f uA %-5s | Q2 E %5.0f mJ, ramp %6.1f ms, SOA ratio %5.2f %s'%(Vb,ihg*1e6,c[0][:4],r['E']*1e3,r['t']*1e3,r['soa'],'OK' if r['soa']<=1 else 'EXCEEDED'))
print('  (m7-split before P7, no C601: 32 V hot cold start SOA ratio 0.97-0.99, Q2 dTj 85-91 K, inrush 36-53 A peak: /workspace/review/split_hp.txt)')
print('\n== 4. Q2 warm restart (C602 charged; from VBAT_P 4 V with U2 restarting, and from Vb/2 with U2 at FULL load at t = 0)')
for Vb in (12.0,13.8,24.0,28.8,32.0):
    for vp0,full in ((4.0,False),(Vb/2,True)):
        for ihg in (39e-6,75e-6):
            for c in (COLD,HOT):
                r=run(Vb,ihg,c,vp0=vp0,warm=True,u2_full=full); worst=max(worst,r['soa'])
                print('  %4.1f %5.1f V %2.0f uA %-4s | engage %s ms, U2 off %s ms, U2 back %s ms | Q2 E %5.0f mJ, SOA ratio %5.2f %s'%(Vb,vp0,ihg*1e6,c[0][:4],
                      ms(r['t_eng']),ms(r['t_u2off']),ms(r['t_u2on']),r['E']*1e3,r['soa'],'OK' if r['soa']<=1 else 'EXCEEDED'))
for vp0,full in ((4.0,False),(16.0,True)):
    for c in (COLD,HOT):
        r=run(32.0,39e-6,c,vp0=vp0,warm=True,u2_full=full,c602=0.5e-6); worst=max(worst,r['soa'])
        print('  32.0 %5.1f V 39 uA %-4s C602 0.5 uF (derated) | U2 back %s ms | SOA ratio %5.2f'%(vp0,c[0][:4],ms(r['t_u2on']),r['soa']))
print('  Without the hold-off but with C601 (why the hold-off is needed once HGATE is slow):')
for Vb in (24.0,32.0):
    r=run(Vb,39e-6,NOM,vp0=Vb/2,warm=True,u2_full=True,holdoff=False,T=0.15)
    print('  %4.1f %5.1f V no hold-off | SOA ratio %5.2f'%(Vb,Vb/2,r['soa']))
print('\nWORST SOA ratio with the P7 front end, all corners: %.2f (%s)'%(worst,'OK' if worst<=1 else 'EXCEEDED'))
for Vb in (9.0,13.8,24.0,32.0):
    Vi=Vb*33/133
    print('  U2 restart after hold-off release at %4.1f V: %5.1f-%5.1f ms (then 7.5 ms soft start)'%(Vb,12.4*math.log((Vi-0.45)/(Vi-1.17)),27.3*math.log((Vi-0.45)/(Vi-1.29))))
if worst>1: sys.exit(1)
