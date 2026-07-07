import sys
from PIL import Image
import numpy as np
page=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a=np.array(im); H,W=a.shape
b=(a<180).astype(np.uint8)
# all X clusters in data region, low threshold
data=b[245:1150,660:1500]; cs=data.sum(axis=0); x=0
print("all X col clusters (center,ink):")
while x<cs.shape[0]:
    if cs[x]>0:
        xs=x
        while x<cs.shape[0] and cs[x]>0: x+=1
        s=int(cs[xs:x].sum())
        if s>5: print((xs+x)//2+660, s)
    else: x+=1
# band heights
rs=b[:,120:600].sum(axis=1); bands=[]; y=0
while y<H:
    if rs[y]>3:
        y0=y
        while y<H and rs[y]>3: y+=1
        bands.append((y0,y))
    else: y+=1
data=[bd for bd in bands if (bd[0]+bd[1])//2>250]
print("row bands (idx,y0,y1,height):")
for i,(y0,y1) in enumerate(data): print(i+1,y0,y1,y1-y0)
