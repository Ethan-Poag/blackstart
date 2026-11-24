"""Rail-cut + Q70/Q71 dissipation, junction temperature and copper width. Ambient 104 F (40 C). Output in F.
Datasheet values (LCSC PDFs in modular_work/fetch):
  SQD40P10-40L (C141570): RDS(on) max 40 mOhm @25 C, 74 mOhm @125 C, 93 mOhm @175 C (VGS -10 V); RthJA 50 C/W (1 in^2 FR-4); TJmax 175 C
  BSC070N10NS5 (C534364): RDS(on) max 7.0 mOhm @25 C (VGS 10 V); RthJA 50 K/W (6 cm^2, 70 um); TJmax 150 C;
                          RDS(on)(Tj) max curve ~1.7x at 150 C [read off Fig. RDS(on)=f(Tj), ESTIMATE of the slope]
  Shunt RLP25FEER002 (C160590): 2 mOhm, 2 W, 2512
Two FETs in parallel per position, even split assumed [ESTIMATE: real split depends on layout; 60/40 case shown too].
Copper: IPC-2221 I = k dT^0.44 A^0.725 (A in mil^2), k 0.048 outer / 0.024 inner, 1 oz outer / 0.5 oz inner ASSUMED (docs/ROUTING_PLAN.md)."""
TA=40.0
F=lambda c:c*9/5+32; dF=lambda k:k*9/5
def rds_sqd(t): return 0.040+(0.074-0.040)*(t-25)/100 if t<=125 else 0.074+(0.093-0.074)*(t-125)/50
def rds_bsc(t): return 0.0070*(1+0.7*(t-25)/125)
def tj(I,rds,rth):
    t=TA
    for _ in range(200): t=TA+rth*I*I*rds(t)
    return t,I*I*rds(t)
def width(I,dT_C,oz,k):
    th=1.378*oz; A=(I/(k*dT_C**0.44))**(1/0.725); return A/th*0.0254
rows=[]
for tot in (7.6,10.0):
    for name,rds,rth,share in (('Q70/Q71 SQD40P10-40L (each, 50/50)',rds_sqd,50,0.5),('Q70/Q71 SQD40P10-40L (hot FET, 60/40)',rds_sqd,50,0.6),
                               ('Ideal-diode LM74700-Q1 + 1x BSC070N10NS5 (single FET)',rds_bsc,50,1.0),
                               ('Rail-cut BSC070N10NS5 (each, 50/50)',rds_bsc,50,0.5),('Rail-cut BSC070N10NS5 (hot FET, 60/40)',rds_bsc,50,0.6)):
        t,p=tj(tot*share,rds,rth); rows.append((tot,name,tot*share,p,F(t),dF(t-TA)))
    rows.append((tot,'Shunt 2 mOhm 2512 (2 W)',tot,tot*tot*0.002,None,None))
print('| Total A | Part | A in part | Loss W | Tj °F | Rise °F |'); print('|---|---|---|---|---|---|')
for r in rows: print('| %.1f | %s | %.1f | %.2f | %s | %s |'%(r[0],r[1],r[2],r[3],'%.0f'%r[4] if r[4] else '-','%.0f'%r[5] if r[5] else '-'))
print()
print('| Current | 1 oz outer, 18 °F rise | 1 oz outer, 36 °F rise | 2 oz outer, 18 °F rise | 0.5 oz inner, 18 °F rise |'); print('|---|---|---|---|---|')
for I in (7.6,10.0):
    print('| %.1f A | %.1f mm | %.1f mm | %.1f mm | %.1f mm |'%(I,width(I,10,1,0.048),width(I,20,1,0.048),width(I,10,2,0.048),width(I,10,0.5,0.024)))
# ---- Pass 1 (M2/N13): slot-bank limiter (TPS48100 + 2x BSC070N10NS5 + 5 mOhm HoJLR2512-3W, VBAT_P -> VBAT_SLOTS) ----
# Same FET model (RthJA 50 K/W, RDS(on) max 7 mOhm x (1 + 0.7 (Tj-25)/125)). Currents: 5.0 A = AUX/slot budget at room,
# 8.61 A = budget + one shorted HSO channel at its 3.61 A max current limit, 9.2 A = lowest bank trip (19.6k, 45.8 mV / 5 mOhm).
print()
print('| Ambient °F | Bank A | Part | A in part | Loss W | Tj °F | Rise °F |'); print('|---|---|---|---|---|---|---|')
for ta in (40.0,65.0):
    for tot in (5.0,8.61,9.2):
        for name,share in (('Bank BSC070N10NS5 (each, 50/50)',0.5),('Bank BSC070N10NS5 (hot FET, 60/40)',0.6)):
            TA=ta; t,p=tj(tot*share,rds_bsc,50)
            print('| %.0f | %.2f | %s | %.2f | %.2f | %.0f | %.0f |'%(F(ta),tot,name,tot*share,p,F(t),dF(t-ta)))
        print('| %.0f | %.2f | Bank shunt 5 mOhm 2512 (3 W) | %.2f | %.2f | - | - |'%(F(ta),tot,tot,tot*tot*0.005))
TA=40.0
