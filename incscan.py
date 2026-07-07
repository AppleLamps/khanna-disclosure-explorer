import sys
from PIL import Image
import numpy as np
page=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a=np.array(im); H,W=a.shape
b=(a<180).astype(np.uint8)
# X clusters in data region x>820 (income area), y 280-1130
data=b[280:1140,820:1500]; cs=data.sum(axis=0); x=0
print("income X col clusters (center,ink):")
while x<cs.shape[0]:
    if cs[x]>0:
        xs=x
        while x<cs.shape[0] and cs[x]>0: x+=1
        s=int(cs[xs:x].sum())
        if s>8: print((xs+x)//2+820, s)
    else: x+=1
# header labels row: find the sub-header text y (None/Dividends...) ~ y 255-275
