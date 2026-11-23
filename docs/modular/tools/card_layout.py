"""Phase 1 card-layout diagram (rear view of the controller, not to scale in detail; rough mm).
Writes docs/modular/card_layout.png and docs/modular/img/connector_options.png."""
import os, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__)); MOD=os.path.dirname(HERE)

def box(ax,x,y,w,h,fc,ec='#222',lw=2,txt=None,fs=15,tc='#111',bold=False,r=2.5):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={r}',fc=fc,ec=ec,lw=lw))
    if txt: ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=fs,color=tc,weight='bold' if bold else 'normal',linespacing=1.15)

fig=plt.figure(figsize=(10.8,16.5),dpi=100)
ax=fig.add_axes([0.02,0.30,0.96,0.62]); ax.set_xlim(-8,292); ax.set_ylim(222,-28); ax.axis('off')
fig.text(0.5,0.975,'Blackstart modular controller (proposal)',ha='center',fontsize=27,weight='bold')
fig.text(0.5,0.948,'Rear view, rough mm. Board 284 x 210 inside today\'s 294 x 226 shell',ha='center',fontsize=16,color='#444')
# mainboard
box(ax,-3.7,-15.3,284,210,'#e9eef5',lw=3,r=4)
ax.text(140,-22,'MAINBOARD / BACKPLANE (fixed, 6-layer)',ha='center',fontsize=17,weight='bold')
# HV side-car
box(ax,-3.7,11,79,164,'#ffd6d6',ec='#b00000',lw=3,txt='HV METER\nCARD\n(dedicated\nslot)\n\n600 V\n2x ADE9000\n4 CTs\n\nown field\nplugs\nJ28 J29 J30\n\nSELV harness\nJ31-J32\n+ ID EEPROM',fs=14,bold=False)
ax.plot([77,77],[5,181],color='#b00000',lw=4,ls='--'); ax.text(36,187,'600 V barrier (shell rib)',color='#b00000',fontsize=13,ha='center',weight='bold')
# bays
slots_top=['LV1','LV2','LV3','LV4']; slots_bot=['LV5','LV6','LV7','LV8']
x0=108; pitch=20
box(ax,x0-3,-14,4*pitch+6,100,'#fff4d6',ec='#c78a00',lw=2.5)
box(ax,x0-3,93,4*pitch+6,100,'#fff4d6',ec='#c78a00',lw=2.5)
use_top=['HSO-5','HSO-5','BRK-4','PAR\n(future)']; use_bot=['DI-8','AI-4','spare','spare']
for i,(s,u) in enumerate(zip(slots_top,use_top)):
    box(ax,x0+i*pitch,-11,14,94,'#ffe08a' if 'spare' not in u else '#ffffff',ec='#7a5200',lw=2,r=1.5)
    ax.text(x0+i*pitch+7,-4,s,ha='center',fontsize=12,weight='bold')
    ax.text(x0+i*pitch+7,40,u,ha='center',va='center',fontsize=13,rotation=90,weight='bold')
for i,(s,u) in enumerate(zip(slots_bot,use_bot)):
    box(ax,x0+i*pitch,96,14,94,'#ffe08a' if 'spare' not in u else '#ffffff',ec='#7a5200',lw=2,r=1.5)
    ax.text(x0+i*pitch+7,103,s,ha='center',fontsize=12,weight='bold')
    ax.text(x0+i*pitch+7,147,u,ha='center',va='center',fontsize=13,rotation=90,weight='bold')
ax.text(x0+2*pitch-3,89.5,'8 universal LV slots, any card',ha='center',va='center',fontsize=11.5,color='#7a5200',weight='bold')
# fixed blocks
box(ax,195,-12,40,42,'#d9f2d9',txt='CM5 +\ndisplay\nEth/USB',fs=12)
box(ax,238,-12,39,42,'#e0e0e0',txt='Power entry\nsupplies\nCAN x2\nRS-485',fs=11.5)
box(ax,195,34,82,46,'#cfe3ff',txt='SAFETY CORE (fixed)\nSTM32, watchdog,\nWD_OK latch, E-stop\nsense/latch, FRAM',fs=11.5,bold=True)
box(ax,195,84,82,56,'#ffd9b3',ec='#a04a00',lw=3,txt='E-STOP RAIL FEED\n+ WATCHDOG RAIL CUT\nJ23 > Q70/Q71 >\nTPS48100 cut\n(WD_OK AND ESTOP_OK)\n> VBAT_ESTOP',fs=10.5,bold=True)
ax.annotate('',xy=(236,145),xytext=(236,140),arrowprops=dict(arrowstyle='-|>',lw=3,color='#a04a00'))
box(ax,195,145,82,47,'#ffc27a',ec='#a04a00',lw=3,txt='ENGINE I/O CARD\n(keyed slot)\nfuel, crank, glow,\nMPU, D+, DI1-4, AI1-2',fs=12.5,bold=True)
ax.add_patch(Rectangle((200,186),6,6,fc='#a04a00',ec='#a04a00')); ax.text(208,189,'coding key',fontsize=11,color='#a04a00',va='center',weight='bold')
box(ax,80,-12,24,204,'#f2f2f2',txt='slot\npower\nswitch\nTPS-\n48100\nx 8\n\nID mux\n2x TCA-\n9548A\nI2C2\n\npresence\n+ fault\nsense',fs=10.5)
# bottom legend
lx=fig.add_axes([0.03,0.015,0.94,0.29]); lx.axis('off'); lx.set_xlim(0,100); lx.set_ylim(0,100)
L=[('#ffe08a','LV cards (power off to swap, ID EEPROM, pluggable field terminals):'),
   (None,'  DI-8   8 digital inputs (DI5-12 today), 76 parts'),
   (None,'  AI-4   4 analog/resistive/4-20 mA inputs (AI3-6), 104 parts'),
   (None,'  HSO-5  5 high-side outputs, 2 A each (AUX1-5 / AUX6-10), 76 parts'),
   (None,'  BRK-4  breaker open/close coils GCB/MCB, 64 parts'),
   (None,'  PAR    future governor/AVR bias card for Ethernet paralleling'),
   ('#ffc27a','ENGINE card: keyed slot, only an engine card fits; no start without it'),
   (None,'  drivers fed from the mainboard E-stop rail; no card = no fuel = stop'),
   ('#cfe3ff','Fixed on the mainboard: STM32, watchdog, E-stop latch/cut, FRAM'),
   (None,'  minimum build = mainboard + ENGINE card + HV card'),
   ('#ffd6d6','HV card keeps its own 600 V plugs; only SELV crosses to the mainboard')]
y=96
for c,t in L:
    if c: lx.add_patch(Rectangle((0,y-4.5),3,6,fc=c,ec='#222'))
    lx.text(4.5 if c else 4.5,y-1.5,t,fontsize=15.5 if c else 15,va='center',weight='bold' if c else 'normal')
    y-=8.7
out=os.path.join(MOD,'card_layout.png'); fig.savefig(out,dpi=100); print(out)

# connector comparison sheet
imgs=[('img/A_din41612_C96_male_RA_9001-11961C00A_C5173361.jpg','A (recommended) DIN 41612 C 96p\ncard side, right-angle male\nWingTAT 9001-11961C00A, LCSC C5173361\n2 A/contact, AC 1000 V 1 min, $1.27'),
      ('img/A_din41612_C96_female_vertical_9001-12961C00A_C5173363.jpg','A (recommended) DIN 41612 C 96p\nmainboard side, vertical female\nWingTAT 9001-12961C00A, LCSC C5173363\n95 mm long, 11.6 mm tall, $1.30'),
      ('img/B_samtec_PCIE-036-02-F-D-TH_C194068.jpg','B (alternative) PCIe x1 card-edge\nSamtec PCIE-036-02-F-D-TH, LCSC C194068\n2.2 A/pin, 1.0 mm pitch, $2.84\nneeds gold fingers on every card'),
      ('img/C_molex_microfit_43045-1600_header.jpg','C (HV card, kept) Molex Micro-Fit 2x8\n43045-1600 (on the BOM today)\nlatched cable harness J31-J32\nonly SELV crosses it')]
f2=plt.figure(figsize=(10.8,13.5),dpi=100)
for i,(p,t) in enumerate(imgs):
    a=f2.add_axes([0.03+(i%2)*0.49,0.60-(i//2)*0.46,0.45,0.32]); a.imshow(Image.open(os.path.join(MOD,p))); a.axis('off')
    f2.text(0.03+(i%2)*0.49+0.225,0.595-(i//2)*0.46,t,ha='center',va='top',fontsize=14.5)
f2.text(0.5,0.975,'Card connector options (LCSC photos)',ha='center',fontsize=24,weight='bold')
o2=os.path.join(MOD,'img','connector_options.png'); f2.savefig(o2,dpi=100); print(o2)
