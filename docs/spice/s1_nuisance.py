#!/usr/bin/env python3
"""Sim 1 nuisance-trip check (m7-split-p7 U45 CRANK / U43 FUEL TPS48100-Q1):
Checks whether C197/C201 = DNP (~10 pF stray) trips on legitimate capacitive/inductive loads, and compares:
  - R301 = 10 R (before Follow-up 1) vs R301 = 22 k (G1PU slew control; R302 G1PD stays 0 R)
  - 2.8 A inductive relay/solenoid (10 mH) + 470 nF / 1 uF EMI cap at 12/24/32 V, worst-case low ISCP (29 k ~ 3.9 A min)
  - Direct 45 A / 0.5 ms pull-in coil (30-60 A class) even with C201 = 4.7 nF / 100 nF (demonstrates R_ISCP 40.2 k / 20 mOhm ~ 4.97 A typ trips direct 30-60 A pull-in; requires interposing relay per INSTALL_SAFETY.md)
Usage: python3 docs/spice/s1_nuisance.py -> docs/spice/results/s1_nuisance_split.txt"""
import os, sys, multiprocessing as mp, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fe import run, F, TVS, integ

def sim(args):
    tag, V, riscp, ctmr, rgpu, cap, mode = args
    for tm, op in ((0.5e-6,''), (0.5e-6,'method=trap reltol=3e-3'), (0.2e-6,'method=trap reltol=3e-3'), (0.2e-6,'reltol=3e-3 trtol=7')):
        try:
            L = [
                f'.include {HERE}/models/TPS48100-Q1_TRANS.lib',
                f'.include {HERE}/models/OptiMOS5_100V_Spice.lib',
                f'.include {HERE}/models/behav.lib',
                f'.include {HERE}/models/small.lib',
                f'Vbat vb 0 PWL(0 0 10u {V})', 'Rb vb nb 15m', 'Lb nb ESTIN 0.5u', 'RQ70 ESTIN VBAT_ESTOP 20m',
                f"XD126 VBAT_ESTOP 0 TVSCA PARAMS: vbr={TVS['SMDJ40CA'][0]} rd={TVS['SMDJ40CA'][1]}",
                'C199 VBAT_ESTOP 0 160n', 'R303 VBAT_ESTOP CRANK_DRN 20m', 'Vtc tc 0 65', 'VQ CRANK_DRN qd 0',
                'XQ47 qd g47 CRANK_OUT tj47 tc BSC070N10NS5 PARAMS: Zthtype=1',
                'XQ48 qd g48 CRANK_OUT tj48 tc BSC070N10NS5 PARAMS: Zthtype=1',
                'Rg47 CRANK_G g47 1', 'Rg48 CRANK_G g48 1',
                f'R301 G1PU CRANK_G {rgpu}', 'R302 G1PD CRANK_G 1m', 'C202 BST CRANK_OUT 470n',
                f"XD69 CRANK_OUT 0 TVSCA PARAMS: vbr={TVS['SMDJ40CA'][0]} rd={TVS['SMDJ40CA'][1]}",
                'D72 0 CRANK_OUT DSS310', 'R352 CRANK_OUT 0 100k',
                'R298 VBAT_ESTOP EN 100k', 'R299 EN 0 27k',
                'VINP INP1 0 PWL(0 0 18m 0 18.01m 5)',
                'RFLT FLT VPU 10k', 'VPU VPU 0 3.3',
                f'R300 ISCP 0 {riscp}', f'C201 TMR 0 {ctmr}',
                'XU45 BST CRANK_DRN VBAT_ESTOP 0 EN FLT G1PD G1PU G2 0 INP1 0 ISCP 0 CRANK_OUT TMR VBAT_ESTOP TPS48100-Q1_TRANS',
                'Ls CRANK_OUT ls1 0.5u', 'Rd2 ls1 ls2 12m',
            ]
            if mode == 'cap':
                L += ['Resr ls2 ce 20m', f'Cemi ce 0 {cap}', f'Rcoil ls2 lc {V/2.8:.4f}', 'Lcoil lc 0 10m']
            elif mode == 'pullin':
                L += [f'Rcoil ls2 lc {V/45.0:.4f}', 'Lcoil lc 0 0.5m']
            r = run(L, ['i(VQ)', 'v(CRANK_OUT)', 'v(qd,CRANK_OUT)', 'v(tj47)', 'v(VBAT_ESTOP)', 'v(FLT)'], 20e-3, tm, f'nuis2_{tag}', tmax=tm, opts=op, timeout=240)
            t = r['t']
            if t[-1] < 19.5e-3: raise RuntimeError(f'end {t[-1]}')
            m = t >= 17.99e-3
            E = integ(t, np.maximum(r['v(qd,CRANK_OUT)'],0)*np.maximum(r['i(VQ)'],0), 17.99e-3) / 2.0
            vout = float(r['v(CRANK_OUT)'][-1]); flt = float(r['v(FLT)'][m].min())
            st = 'PASS_ON' if (vout > 0.8*V and flt > 2.5) else 'TRIPPED'
            return (tag, V, riscp, ctmr, rgpu, cap, float(r['i(VQ)'][m].max()), vout, float(r['v(VBAT_ESTOP)'][m].max()), flt, float(r['v(tj47)'][m].max()), E*1e3, st)
        except Exception as e:
            err = str(e)[:80]
    return (tag, V, riscp, ctmr, rgpu, cap, -1, -1, -1, -1, -1, -1, 'ERR:'+err)

if __name__ == '__main__':
    jobs = [
        # Baseline (R301=10R, C201=DNP 10p): false-trips on 470nF EMI cap at 32V
        ('c470n_10p_r10_32V',  32, '40.2k', '10p',  10,    '470n', 'cap'),
        # Fix (R301=22k, C201=DNP 10p): rides through 470nF and 1uF EMI caps across 12/24/32V even at min ISCP (29k ~ 3.9 A)
        ('c470n_10p_r22k_12V', 12, '29.0k', '10p',  22000, '470n', 'cap'),
        ('c470n_10p_r22k_24V', 24, '29.0k', '10p',  22000, '470n', 'cap'),
        ('c470n_10p_r22k_32V', 32, '29.0k', '10p',  22000, '470n', 'cap'),
        ('c1u_10p_r22k_12V',   12, '29.0k', '10p',  22000, '1u',   'cap'),
        ('c1u_10p_r22k_24V',   24, '29.0k', '10p',  22000, '1u',   'cap'),
        ('c1u_10p_r22k_32V',   32, '29.0k', '10p',  22000, '1u',   'cap'),
        # Direct 45 A pull-in coil trips regardless of TMR (4.7nF, 100nF) because R_ISCP 40.2k / 20mOhm = 4.97 A typ
        ('pull45_4n7_r10_24V', 24, '40.2k', '4.7n', 10,    '0',    'pullin'),
        ('pull45_100n_r10_24V',24, '40.2k', '100n', 10,    '0',    'pullin'),
    ]
    out = [__doc__, '', 'case                  Vb   ISCP   TMR   G1PU   Cemi | Ipk     Vout    VBAT_E  FLT_min  Tj_max  E/FET   status']
    with mp.Pool(8) as P:
        for x in P.map(sim, jobs, chunksize=1):
            out.append(f'{x[0]:21s} {x[1]:2.0f}V {x[2]:6s} {x[3]:5s} {x[4]:5d}R {x[5]:4s} | {x[6]:6.2f}A {x[7]:6.2f}V {x[8]:6.2f}V {x[9]:5.2f}V  {x[10]:5.1f}C {x[11]:5.2f}mJ {x[12]}')
    txt = '\n'.join(out)
    print(txt)
    open(os.path.join(HERE, 'results', 's1_nuisance_split.txt'), 'w').write(txt + '\n')
