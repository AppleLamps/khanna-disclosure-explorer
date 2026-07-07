import sys
from PIL import Image
import numpy as np

page=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a=np.array(im); H,W=a.shape
b=(a<120).astype(np.uint8)

# ---- find asset name rows (left text block) ----
left = b[:,120:600]
rs = left.sum(axis=1)
rows=[]
y=0
while y<H:
    if rs[y]>2:
        y0=y
        while y<H and rs[y]>2: y+=1
        y1=y
        if y1-y0>=3:
            rows.append((y0,y1))
    else:
        y+=1
# merge close bands (<6px gap)
merged=[]
for band in rows:
    if merged and band[0]-merged[-1][1]<5:
        merged[-1]=(merged[-1][0],band[1])
    else:
        merged.append(band)
print("num name rows:", len(merged))

# ---- find matrix columns from header/all ink ----
mx0=640
mat=b[:, mx0:]
cs=mat.sum(axis=0)
# find peaks: contiguous cols with ink
cols=[]
x=0
Wm=cs.shape[0]
while x<Wm:
    if cs[x]>1:
        x0=x
        while x<Wm and cs[x]>1: x+=1
        x1=x
        cols.append(((x0+x1)//2 + mx0, cs[x0:x1].sum(), x0+mx0, x1+mx0))
    else:
        x+=1
print("col clusters (center, inksum, x0, x1):")
for c in cols: print(c)
