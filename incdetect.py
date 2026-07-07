import sys
from PIL import Image
import numpy as np
page=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a=np.array(im); H,W=a.shape
b=(a<180).astype(np.uint8)
labels=["NONE","DIVIDENDS","RENT","INTEREST","CAPITAL GAINS","EXCEPTED/BLIND TRUST","TAX-DEFERRED","PARTNERSHIP INCOME"]
centers=[943,1006,1067,1130,1192,1266,1329,1417]
rs=b[:,120:600].sum(axis=1); bands=[];y=0
while y<H:
    if rs[y]>3:
        y0=y
        while y<H and rs[y]>3:y+=1
        if y-y0>=3: bands.append((y0,y))
    else:y+=1
data=[bd for bd in bands if (bd[0]+bd[1])//2>250]
print(f"page {page}: {len(data)} data rows")
# check value region and eif
print("value-region ink x755-810:", int(b[280:1140,755:810].sum()), " EIF x845-895:", int(b[280:1140,845:895].sum()))
for i,(y0,y1) in enumerate(data):
    win=b[max(y0-1,281):y1+1,:]
    marks=[]
    for k,cx in enumerate(centers):
        ink=int(win[:,cx-20:cx+20].sum())
        if ink>=12: marks.append((labels[k],ink))
    m=", ".join(f"{n}:{v}" for n,v in marks) if marks else "(none detected)"
    print(f"{i+1:2d} {m}")
