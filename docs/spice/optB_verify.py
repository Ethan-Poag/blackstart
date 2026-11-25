#!/usr/bin/env python3
"""Verify as-drawn Option B schematic on m7-modular or m7-split-p7:
1. Sim 1 (32 V worst-L dead short, unloaded + loaded) and Sim 1b recovery (12 V & 32 V).
2. Sim 5 ride-through (12/24/32 V, O and G types, 0.1-20 ms, 39/75 uA HGATE) from as-drawn Option B.
Usage: optB_verify.py mod|split"""
import sys, os, multiprocessing as mp, numpy as np
from fe import *
import s1_short as S1, s1b_recover as S1B

T0 = 0.5e-3

def one_s1(args):
    br, load, case = args
    V, Rb, Lb, Rd2, cold, Lbank, tresp = 32.0, 0.015, 2e-6, 0.025, 1, 150e-9, 1.5
    isat = 60.0 if case == 'realistic' else 1e6
    p = dict(V=V, Rb=Rb, Lb=Lb, cold=cold, branch=br,
             u2=dict(ss0=1) if load else None, u5=dict() if load else None,
             opt_b=True, c_hu=160e-6)
    L = frontend(p)
    cs = 8 * (2.2e-6 * 0.5 + 0.1e-6 * 0.63) + 2.2e-6 * 0.5 + 0.1e-6 * 0.63
    L += ['Lbank VBAT_P bk1 %g' % Lbank, 'Rd1 bk1 VBAT_SLOTS 10m', 'CS VBAT_SLOTS 0 %g' % cs,
          'VEF VBAT_SLOTS efin 0', 'XEF efin OUT TPS16630B PARAMS: ron=19m iscp=45 tresp=%g iol=6.30 isat=%g' % (tresp, isat),
          'DSCH 0 OUT DSS310', 'ROUT OUT 0 1k', 'Ls OUT ls1 50n', 'Rd2 ls1 ls2 %g' % Rd2, 'Ssh ls2 0 shc 0 SWSH',
          '.model SWSH SW(Ron=1m Roff=1G Vt=0.5 Vh=0.1)', 'Vsh shc 0 PWL(0 0 %g 0 %g 1)' % (S1.T_SH, S1.T_SH + 1e-9)]
    name = 'optB_s1_%s_%s_%s' % (br, 'L' if load else 'U', case[0])
    r = run(L, S1.PROBES, 80e-6, 2e-9, name, tmax=5e-9, nodeset=ns_on(V, br))
    t = r['t']; m = t >= S1.T_SH
    tv = lambda k, s=1: float((s * r[k][m]).max() * s)
    v1, r1 = TVS['SMDJ40CA']; v2, r2 = TVS['SMBJ40CA']
    vb = r['v(BAT_IN)']; vp = r['v(VBAT_P)']
    eD1 = integ(t, vb * np.maximum(vb - v1, 0) / r1)
    eD2 = integ(t, vp * np.maximum(vp - v2, 0) / r2)
    return (load, case), dict(
        vP=tv('v(VBAT_P)'), vB=tv('v(BAT_IN)'), vS=tv('v(VBAT_SLOTS)'), vU=tv('v(U65_IN)'),
        ief=float(r['i(VEF)'].max()), iL=float(r['i(Lb)'].max()), iq2=float(r['i(VQ2)'].max()),
        tj2=float(r['v(tj2)'].max()), eD1=eD1, eD2=eD2, i2t=integ(t, r['i(Lb)']**2),
        u5enmin=tv('v(U5_EN)', -1), ho=float(r['v(HO_F)'].max()), warn=r.get('_warn'))

def one_s1b(args):
    br, V, Rd2, Lbank = args
    p = dict(V=V, Rb=0.015, Lb=2e-6, cold=1, branch=br, u2=dict(ss0=1), u5=dict(), opt_b=True, c_hu=160e-6)
    L = frontend(p)
    cs = 8 * (2.2e-6 * 0.5 + 0.1e-6 * 0.63) + 2.2e-6 * 0.5 + 0.1e-6 * 0.63
    L += ['Lbank VBAT_P bk1 %g' % Lbank, 'Rd1 bk1 VBAT_SLOTS 10m', 'CS VBAT_SLOTS 0 %g' % cs,
          'VEF VBAT_SLOTS efin 0', 'XEF efin OUT TPS16630B PARAMS: ron=19m iscp=45 tresp=1.5 iol=6.30 isat=1e6',
          'DSCH 0 OUT DSS310', 'ROUT OUT 0 1k', 'Ls OUT ls1 50n', 'Rd2 ls1 ls2 %g' % Rd2, 'Ssh ls2 0 shc 0 SWSH',
          '.model SWSH SW(Ron=1m Roff=1G Vt=0.5 Vh=0.1)', 'Vsh shc 0 PWL(0 0 %g 0 %g 1)' % (S1.T_SH, S1.T_SH + 1e-9)]
    name = 'optB_s1b_%s_%g_%g' % (br, V, Lbank * 1e9)
    r = run(L, ['v(VBAT_P)', 'v(BAT_IN)', 'v(VBAT_DD,VBAT_PS)', 'i(VQ2)', 'v(tj2)', 'v(HGATE,VBAT_P)', 'v(xu2.runs)', 'v(U5_ALIVE)'],
            80e-3, 20e-9, name, tmax=0.2e-6, nodeset=ns_on(V, br), timeout=6000)
    t = r['t']; m = t > S1.T_SH
    alive = (r['v(U5_ALIVE)'] > 0.5) | (r['v(xu2.runs)'] > 0.5)
    f = lambda c: first(t[m], c[m])
    return args, dict(
        dead=f(~alive), u2d=f(r['v(xu2.runs)'] < 0.5), u5d=f(r['v(U5_ALIVE)'] < 0.5),
        soa=soa(r, t0=S1.T_SH), tj=float(r['v(tj2)'].max()),
        vgs_on=S1B.rec(t, r['v(HGATE,VBAT_P)']), vpmin=float(r['v(VBAT_P)'][m].min()),
        vp_end=float(r['v(VBAT_P)'][-1]), warn=r.get('_warn'))

def one_s5(a):
    br, V, typ, ti, ihg = a
    p = dict(V=V, Rb=0.015, Lb=0.5e-6, branch=br, ihg=ihg, u2=dict(ss0=1), u5=dict(),
             bat_switch=True, bat_short=(typ == 'G'), r_short=1.0, opt_b=True, c_hu=160e-6,
             extra=['Vbsw bsw 0 PWL(0 1 %.9g 1 %.9g 0 %.9g 0 %.9g 1)' % (T0, T0 + 1e-6, T0 + ti, T0 + ti + 1e-6)]
             + (['Vbsh bsh 0 PWL(0 0 %.9g 0 %.9g 1 %.9g 1 %.9g 0)' % (T0, T0 + 1e-6, T0 + ti, T0 + ti + 1e-6)] if typ == 'G' else []))
    ns = ns_on(V, br)
    ns.update({'xu1.uvs': 1, 'xu1.offs': 0, 'xu2.runs': 1, 'xu2.ss': 1})
    tst = T0 + ti + 1.1 * V / (ihg / (C601_DEFAULT + 1e-9)) + 14e-3
    name = 'optB_s5_%s_%g_%s_%g_%g' % (br, V, typ, ti * 1e3, ihg * 1e6)
    try:
        for tm, op in ((5e-6, ''), (1e-6, ''), (0.5e-6, ''), (1e-6, 'reltol=3e-3 trtol=7')):
            r = run(frontend(p), ['v(BAT_IN)', 'v(VBAT_P)', 'v(U5VIN)', 'v(VBAT_DD,VBAT_PS)', 'i(VQ2)', 'v(tj2)', 'v(xu2.runs)', 'v(U5_ALIVE)', 'v(HO_F)'],
                    tst, 2e-6, name, tmax=tm, opts=op, nodeset=ns)
            t = r['t']; vpre = float(np.interp(T0 - 10e-6, t, r['v(VBAT_P)'])) if len(t) and t[-1] > T0 else 0.0
            if t[-1] >= T0 + ti + 0.5e-3 and vpre >= 0.8 * V:
                break
        else:
            return dict(a=a, error='ended at %.3g s (vpre=%.2f V)' % (t[-1], vpre))
        alive = (r['v(U5_ALIVE)'] > 0.5) | (r['v(xu2.runs)'] > 0.5)
        m = t > T0; dead = first(t[m], ~alive[m])
        u5d = first(t[m], r['v(U5_ALIVE)'][m] < 0.5); u2d = first(t[m], r['v(xu2.runs)'][m] < 0.5)
        return dict(a=a, survive=dead is None, tdead=(dead - T0) if dead else None,
                    u5d=(u5d - T0) if u5d else None, u2d=(u2d - T0) if u2d else None,
                    soa=soa(r, t0=T0 + ti), tj=float(r['v(tj2)'].max()),
                    E=integ(t, np.maximum(r['v(VBAT_DD,VBAT_PS)'], 0) * np.maximum(r['i(VQ2)'], 0), T0 + ti),
                    vp_ret=float(np.interp(T0 + ti, t, r['v(VBAT_P)'])),
                    iq2=float(r['i(VQ2)'][t > T0 + ti].max()), warn=r.get('_warn'))
    except Exception as e:
        return dict(a=a, error=str(e)[:300])

if __name__ == '__main__':
    br = sys.argv[1]
    # 1. s1 + s1b
    with mp.Pool(4) as P:
        R1 = P.map(one_s1, [(br, True, 'pessimistic'), (br, True, 'realistic')])
        R1B = P.map(one_s1b, [(br, 12.0, 0.012, 150e-9), (br, 32.0, 0.025, 60e-9), (br, 32.0, 0.025, 150e-9)])

    out1 = ['Sim 1 (%s as-drawn Option B): 32 V worst-L dead short (Rb=15m, Lb=2uH, Rd2=25m, cold=1, Lbank=150nH, tresp=1.5us)' % br,
            'mode      case        VBAT_P  BAT_IN  VBAT_SLOTS  U65    eFuse   harness  Q2 Ipk  Q2 Tj        F1 I2t   U5_EN min  HO_F max']
    for (load, case), x in R1:
        out1.append('%-9s %-11s %5.1fV  %5.1fV  %7.1fV   %5.1fV  %4.0fA   %4.0fA    %4.0fA   %4.0fF (%3.0fC)  %.4f   %5.2fV     %4.2fV' % (
            'loaded' if load else 'unloaded', case, x['vP'], x['vB'], x['vS'], x['vU'], x['ief'], x['iL'], x['iq2'], F(x['tj2']), x['tj2'], x['i2t'], x['u5enmin'], x['ho']))
    out1.append('\nSim 1b recovery (%s as-drawn Option B, C601=100nF):' % br)
    g = lambda v: ('%7.3f ms' % (v * 1e3)) if v is not None else '     none'
    for args, x in R1B:
        s = x['soa']
        out1.append('%4.1f V Lbank=%3.0fnH | VBAT_P min/end %5.2f/%5.2fV | MCU %-5s (%s / %s) | Q2 Vgs>8V %s | Q2 Tj %4.0fF (%3.0fC) | SOA %.2f' % (
            args[1], args[3] * 1e9, x['vpmin'], x['vp_end'], 'alive' if x['dead'] is None else 'RESET',
            g(x['u2d']), g(x['u5d']), g(x['vgs_on']), F(x['tj']), x['tj'], s[0]))
    txt1 = '\n'.join(out1)
    print(txt1, flush=True)
    open(os.path.join(HERE, 'results', 's1_short_%s_optB.txt' % br), 'w').write(txt1 + '\n')

    # 2. s5 ride-through from as-drawn Option B
    TI = [0.1e-3, 0.2e-3, 0.5e-3, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3]
    J5 = [(br, V, typ, ti, ihg) for V in (12.0, 24.0, 32.0) for typ in ('O', 'G') for ti in TI for ihg in (39e-6, 75e-6)]
    with mp.Pool(8) as P:
        R5 = P.map(one_s5, J5, chunksize=1)

    out5 = ['Sim 5 (%s as-drawn Option B): battery interruption 0.1-20 ms, C38+C39 on U5_VIN, 2x 100u hold-up (160u cold/aged)' % br,
            'Vb   type  t_int ms  HGATE | VBAT_P at return  MCU   (U2 off / U5 off ms) | Q2 Ipk  Q2 E mJ  Tj max         SOA ratio']
    f = lambda v: '%6.2f' % (v * 1e3) if v is not None else '     -'
    bad = [x for x in R5 if 'error' in x]; ok_runs = [x for x in R5 if 'error' not in x]
    for x in ok_runs:
        _, V, typ, ti, ihg = x['a']; s = x['soa']
        out5.append('%4.1f  %s   %6.1f    %2.0f uA | %6.1f V          %-5s (%s / %s) | %5.0fA %6.1f  %4.0f F (%3.0f C)  %.2f%s' % (
            V, typ, ti * 1e3, ihg * 1e6, x['vp_ret'], 'alive' if x['survive'] else 'RESET',
            f(x['u2d']), f(x['u5d']), x['iq2'], x['E'] * 1e3, F(x['tj']), x['tj'], s[0],
            '  WARN ' + x['warn'] if x['warn'] else ''))
    out5.append('\nSummary (%s as-drawn Option B):' % br)
    for V in (12.0, 24.0, 32.0):
        for typ in ('O', 'G'):
            S = [x for x in ok_runs if x['a'][1] == V and x['a'][2] == typ]
            ok = [ti for ti in TI if any(x['a'][3] == ti for x in S) and all(x['survive'] for x in S if x['a'][3] == ti)]
            lc = 0
            for ti in TI:
                if ti in ok: lc = ti
                else: break
            out5.append('  %4.1f V type %s: MCU survives up to %s ms (first reset at %s ms); worst SOA %.2f' % (
                V, typ, ('%g' % (lc * 1e3)) if lc else '<0.1',
                ('%g' % (min([ti for ti in TI if ti not in ok]) * 1e3)) if len(ok) < len(TI) else '>20',
                max([x['soa'][0] for x in S] or [float('nan')])))
    out5.append('\nFailed runs: %d' % len(bad))
    for x in bad:
        out5.append('  %s: %s' % (x['a'], x['error']))
    txt5 = '\n'.join(out5)
    print(txt5, flush=True)
    open(os.path.join(HERE, 'results', 's5_ride_%s_optB.txt' % br), 'w').write(txt5 + '\n')
