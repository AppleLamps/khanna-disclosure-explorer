import sys
from PIL import Image
import numpy as np
page=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a=np.array(im); H,W=a.shape
b=(a<180).astype(np.uint8)
# header Max row: find y band of the two number rows in matrix region x>=680
mat=b[:,680:1470]
rs=mat.sum(axis=1)
# print top ink rows (y<260)
for y in range(140,260):
    if rs[y]>3: print(y, rs[y])
