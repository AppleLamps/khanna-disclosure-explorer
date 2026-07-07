import sys
from PIL import Image
import numpy as np
page=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a=np.array(im); H,W=a.shape
b=(a<180).astype(np.uint8)
y0,y1=245,1150
data=b[y0:y1,660:1470]
cs=data.sum(axis=0)
cols=[]; x=0
while x<cs.shape[0]:
    if cs[x]>0:
        xs=x
        while x<cs.shape[0] and cs[x]>0: x+=1
        cols.append((xs+660, x+660, int(cs[xs:x].sum())))
    else: x+=1
print("X-mark column clusters (x0,x1,ink):")
for c in cols: 
    if c[2]>15: print(c, "center", (c[0]+c[1])//2)
