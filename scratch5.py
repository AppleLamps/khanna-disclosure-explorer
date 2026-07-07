import sys
from PIL import Image
import numpy as np
page=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a=np.array(im); H,W=a.shape
b=(a<180).astype(np.uint8)
# use both header number rows y 167-201
hdr=b[167:202,:]
cs=hdr.sum(axis=0)
cols=[]; x=0
while x<W:
    if cs[x]>0:
        x0=x
        while x<W and cs[x]>0: x+=1
        cols.append(((x0+x)//2, x0, x))
    else: x+=1
cols=[c for c in cols if c[0]>650]
print("num header col clusters:",len(cols))
for c in cols: print(c)
