import sys
from PIL import Image
import numpy as np
page=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a=np.array(im); H,W=a.shape
b=(a<180).astype(np.uint8)
buckets=["None","$1-$1,000","$1,001-$15,000","$15,001-$50,000","$50,001-$100,000",
"$100,001-$250,000","$250,001-$500,000","$500,001-$1,000,000","$1,000,001-$5,000,000",
"$5,000,001-$25,000,000","$25,000,001-$50,000,000","Over $50,000,000"]
centers=[round(780+55.5*k) for k in range(12)]
rs=b[:,120:600].sum(axis=1)
bands=[]; y=0
while y<H:
    if rs[y]>3:
        y0=y
        while y<H and rs[y]>3: y+=1
        if y-y0>=3: bands.append((y0,y))
    else: y+=1
data=[bd for bd in bands if (bd[0]+bd[1])//2>250]
print(f"page {page}: {len(data)} data rows")
for i,(y0,y1) in enumerate(data):
    win=b[y0-1:y1+1,:]
    eif=int(win[:,648:702].sum())
    inks=[int(win[:,cx-24:cx+24].sum()) for cx in centers]
    order=sorted(range(12),key=lambda k:-inks[k])
    best=order[0]; second=order[1]
    label=buckets[best] if inks[best]>=12 else "??"
    flag=""
    if inks[best]<12: flag=" LOW"
    if inks[second]>=14 and inks[second]>0.5*inks[best]: flag+=f" AMBIG(2nd={buckets[second]}:{inks[second]})"
    e = f" EIF={eif}" if eif>=12 else ""
    print(f"{i+1:2d} c{best:2d} {label:20s} ink={inks[best]:4d}{e}{flag}")
