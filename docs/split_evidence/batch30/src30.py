import re,sys,os
os.chdir('/workspace/m7/split')
D='2026-11-22 ~12:08 HST'
J2=f"ALT (Batch 30): JLC live {D}: C5199898 JLC 93 / LCSC 87 (was 1 on 2026-11-21). Drop-in alternate, same Samtec footprint and pinout: FTSH-105-01-F-DV C6620841 (gold-flash contacts, JLC 187 / LCSC 180). If neither is in stock on order day: CONSIGN FTSH-105-01-L-DV from Samtec direct or Digi-Key and ship to JLC, or hand-fit J2 before first flash (SWD is needed for bring-up)"
TPS=f"CONSIGN (Batch 30): JLC/LCSC stock 0 live {D} (was 12). Buy TPS1H200AQDGNRQ1 from the TI store (live 57,237) or Digi-Key/Mouser and ship 2/board to JLC. No pin-compatible second part; recheck on order day"
LMR=f"STOCK RISK (Batch 30): JLC/LCSC 16 live {D} (enough for ~16 boards). Second source TI store LMR36506RRPER (live 5,999) or Digi-Key/Mouser, consign. Pin-compatible fallback LMR36506RFRPER (same RT/FB circuit, FPWM at light load = higher battery drain; DS Device Comparison table); JLC 0, TI store 10,100"
DSI=f"STOCK RISK (Batch 30): JLC 81 / LCSC 51 live {D}; JLC price now 6.46 USD (TI store 2.13 at 1ku). Second source TI store SN65DSI83ZXHR (live 2,123) or Digi-Key/Mouser, consign. No verified drop-in in another package"
MOV=f"STOCK RISK (Batch 30): JLC/LCSC 25 live {D} = 4 boards at 6/board. Second source TMOV20RP460E bulk (same 20 mm body, 460 V in-line leads e1 0-2.0 mm per DS, fits the 7.5 mm footprint; trim the 25.4 mm leads) from Digi-Key/Mouser/Littelfuse distribution, consign or hand-fit (THT)"
M={'J2':('mcu.kicad_sch',J2),'U15':('comms.kicad_sch',TPS),'U16':('comms.kicad_sch',TPS),'U5':('power.kicad_sch',LMR),'U21':('display.kicad_sch',DSI)}
for i in range(1,7): M[f'RV{i}']=('ac_metering.kicad_sch',MOV)
for ref,(f,txt) in M.items():
    L=open(f).read().split('\n'); n=[i for i,l in enumerate(L) if l.startswith(f'(property "Reference" "{ref}"')]
    assert len(n)==1,(ref,n); i=n[0]
    j=i
    while not L[j].startswith('(instances'):
        assert not L[j].startswith('(property "Sourcing"'),ref; j+=1
    k=[x for x in range(i,j) if L[x].startswith('(property "Manufacturer"')][0]
    at=re.search(r'\(at [^)]*\)',L[k]).group(0)
    L.insert(k+1,f'(property "Sourcing" "{txt}" {at} (effects (font (size 1.27 1.27)) hide))')
    open(f,'w').write('\n'.join(L)); print(ref,f,'ok')
