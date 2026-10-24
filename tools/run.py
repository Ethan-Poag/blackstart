import sys; sys.path.insert(0,'.')
from design import *
write_project()
flagged,ns=build(SHEETS)
open('../docs/auto_nc_pins.log','w').write('\n'.join(NCLOG)+'\n')
print('flags',flagged); print('NC count',len(NCLOG))
