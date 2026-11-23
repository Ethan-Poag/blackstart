"""Cost delta of the recommended modular build (example build 2 = baseline-equivalent I/O) vs the one-board baseline.
Prices: LCSC live 2026-11-23 ~10:09 AM HST [M-LCSC], repo BOM bom/genctl_main_bom.csv [M-BOM], or estimate [E]."""
import csv,os
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows=[]  # (group, item, qty_per_unit, unit_q1, unit_q10, source)
def add(g,i,q,p1,p10,src): rows.append((g,i,q,p1,p10,src))
S=8  # LV slots on the backplane
# per-slot backplane parts
add('backplane x8','DIN 41612 C 96p female vertical, WingTAT 9001-12961C00A (C5173363)',S,1.3035,1.0953,'M-LCSC')
add('backplane x8','TPS48100QDGXRQ1 slot VBAT_FIELD switch (C43131316)',S,3.5209,3.12,'M-BOM')
add('backplane x8','BSC070N10NS5 back-to-back FETs (C534364)',2*S,0.4647,0.2962,'M-BOM')
add('backplane x8','Slot shunt 2512 (priced as the 20 mOhm FMF25FPJR020-LH C105360; 10 mOhm part to pick)',S,0.0655,0.0655,'M-BOM proxy')
add('backplane x8','TPS2553DBVR +5V_SLOT and +3V3_SLOT switches (C55266)',2*S,0.5563,0.4614,'M-BOM')
add('backplane x8','74LVC1G08 OUT_EN = WD_OK AND SLOT_EN (C176929)',S,0.0868,0.0694,'M-BOM')
add('backplane x8','Passives per slot (~10)',S,0.10,0.10,'E')
add('backplane shared','TCA9548APWR I2C mux for card ID EEPROMs (C130026)',1,0.8659,0.732,'M-LCSC')
add('backplane shared','TCA9555PWR x2 slot PRESENT/INT/FAULT/EN (C465732)',2,0.7314,0.517,'M-BOM')
add('backplane shared','TMUX1208PWR 8:1 mux, slot ANA_OUT lines -> one STM32 ADC pin (C494728)',1,0.571,0.4598,'M-BOM')
add('backplane shared','3-to-8 chip-select decoder (part to pick) + passives',1,0.25,0.25,'E')
# per-card overhead, example build 2: DI-8, AI-4, HSO-5 x2, BRK-4 + HV
cards={'DI-8':1,'AI-4':1,'HSO-5':2,'BRK-4':1}
nc=sum(cards.values())
add('cards','DIN 41612 C 96p male right-angle, WingTAT 9001-11961C00A (C5173361)',nc,1.2659,1.061,'M-LCSC')
add('cards','AT24CS32-STUM-T ID/cal EEPROM (C147891)',nc+1,1.4297,1.1721,'M-LCSC')
add('cards','MCP23S17T-E/SS SPI expander (C128577) on DI-8, HSO-5 x2, BRK-4',4,1.7271,1.4661,'M-LCSC')
add('cards','SN74LVC541APWR OE-gated output buffer (C113281) on HSO-5 x2, BRK-4',3,0.5939,0.4745,'M-BOM')
add('cards','TMUX1208PWR current-sense mux (C494728) on HSO-5 x2, BRK-4',3,0.571,0.4598,'M-BOM')
add('cards','TCA9555PWR on AI-4 (excitation/shunt enables) (C465732)',1,0.7314,0.517,'M-BOM')
add('cards','DI-8 own bias switch block (copy of DI_BIAS, ~10 parts)',1,1.00,0.80,'E')
add('cards','Card passives (~6 per card) + 1 extra field header KF2EDGRM-5.08-6P net',nc+1,0.41,0.34,'E')
# boards and fees
designs=4
add('boards','LV card PCB, 4-layer ~100 x 36 mm, 5 pcs per design at qty 1 (per-unit share at qty 10)',designs,8.00,1.20,'E (SPLIT_SCOPE JLC 100x100 4L x5 ~ EUR 5.92)')
add('boards','PCBA fixed fees per extra order: setup 8.18 + stencil 1.53 + hand-solder 3.58 + confirm 0.45',designs,13.74,1.374,'DS (JLC fee table via SPLIT_SCOPE)')
add('boards','Extended-part loading, ~6 unique extended parts per card order at $3.07',designs,18.42,1.842,'DS rate, count E')
add('mechanical','Rear shell card bays (+14 mm), 5 faceplates + guides, captive screws',1,25.00,15.00,'E')
add('mechanical','HV harness 2x8 -> 2x10 for EEPROM I2C (or reuse spare + one GND)',1,1.00,0.80,'E')
t1=t10=0
with open(os.path.join(H,'cost_delta.csv'),'w',newline='') as f:
    w=csv.writer(f); w.writerow(['group','item','qty_per_unit','unit_usd_qty1','unit_usd_qty10','ext_usd_qty1','ext_usd_qty10','source'])
    for g,i,q,p1,p10,s in rows:
        w.writerow([g,i,q,p1,p10,round(q*p1,2),round(q*p10,2),s]); t1+=q*p1; t10+=q*p10
    w.writerow(['TOTAL','delta vs one-board baseline (savings from removed shared mainboard parts NOT subtracted)','','','',round(t1,2),round(t10,2),'mix'])
print(round(t1,2),round(t10,2))
for g in ['backplane x8','backplane shared','cards','boards','mechanical']:
    print(g, round(sum(q*p1 for gg,i,q,p1,p10,s in rows if gg==g),2), round(sum(q*p10 for gg,i,q,p1,p10,s in rows if gg==g),2))
