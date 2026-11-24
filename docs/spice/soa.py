"""BSC070N10NS5 SOA check, copied verbatim from m7-modular docs/modular/tools/kick_calc.py (same as m7-split-p7 tools/p7_calc.py)
so both branches judge the SPICE traces with the hand calc's own criterion."""
import math, numpy as np
# BSC070N10NS5 Diagram 3 (SOA, Tc 77 F / 25 C, single pulse), digitised from the 400 dpi render (docs/split_evidence/modular_pass5/
# bsc070_soa.png): 1 ms, 10 ms and DC lines follow I = A / V^2 (Spirito-limited linear mode); 100 us is piecewise.
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


