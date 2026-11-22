# RETIRED (Batch 30, 2026-11-22 HST): pre-split single-board generator. It predates the two-board split
# (genctl + genctl_meter, 09b60d3) and Batch 27-29 (it would recreate AC1005 CTs, the on-board J9/J30 CT header,
# the old category BOMs and one 'genctl' project). It refuses to run unless BLACKSTART_LEGACY_REGEN=1 is set, and even
# then it must never write into the repo. Edit the committed .kicad_sch files; BOMs come from tools/bom_from_sch.py.
import os as _os, sys as _sys
if _os.environ.get('BLACKSTART_LEGACY_REGEN')!='1':
    _sys.exit('RETIRED: tools/%s is the pre-split generator (see header). Edit the .kicad_sch files; BOMs: tools/bom_from_sch.py' % _os.path.basename(__file__))
import sys; sys.path.insert(0,'.')
from design import *
write_project()
flagged,ns=build(SHEETS)
open('../docs/auto_nc_pins.log','w').write('\n'.join(NCLOG)+'\n')
print('flags',flagged); print('NC count',len(NCLOG))
