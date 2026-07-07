import sys
from PIL import Image
import numpy as np
page=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a=np.array(im); H,W=a.shape
b=(a<180).astype(np.uint8)
def clusters(yb0,yb1,thresh=0,minx=650):
    hdr=b[yb0:yb1,:]; cs=hdr.sum(axis=0); out=[]; x=0
    while x<W:
        if cs[x]>thresh:
            xs=x
            while x<W and cs[x]>thresh: x+=1
            out.append(((xs+x)//2,xs,x))
        else: x+=1
    return [c for c in out if c[0]>minx]
print("MIN row (167-178):"); 
for c in clusters(167,178): print(c)
print("MAX row (190-202):")
for c in clusters(190,202): print(c)
