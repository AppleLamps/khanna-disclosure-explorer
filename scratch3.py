import sys
from PIL import Image
import numpy as np
page=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a=np.array(im); H,W=a.shape
# histogram
print("min/max/mean", a.min(), a.max(), a.mean())
left=a[:,120:600]
print("left region dark pixel counts at thresholds:")
for t in (100,140,160,180,200):
    print(t, (left<t).sum())
# row profile with t=180
b=(a<180).astype(np.uint8)
rs=b[:,120:600].sum(axis=1)
print("rows with ink>3 (t180):", int((rs>3).sum()))
# print band structure
y=0; bands=[]
while y<H:
    if rs[y]>3:
        y0=y
        while y<H and rs[y]>3: y+=1
        bands.append((y0,y))
    else: y+=1
print("num bands t180:", len(bands))
for bnd in bands[:80]: print(bnd, (bnd[0]+bnd[1])//2)
