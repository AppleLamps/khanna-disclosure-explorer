import sys
from PIL import Image
import numpy as np
from scipy import ndimage

page = sys.argv[1]
im = Image.open(f'docs/2019-2/pages/page-{page}.jpg').convert('L')
a = np.array(im); H,W = a.shape
b = (a < 120).astype(np.uint8)

# Matrix region x>=640
mx0=640
matrix = b[:, mx0:]
# row projection to find header and data rows
rowsum = matrix.sum(axis=1)
print("=== rows with ink (y, sum) ===")
ys=[y for y in range(H) if rowsum[y]>0]
print("y range with ink:", ys[0], ys[-1])
# Find header digit band vs data. Print row profile coarse
for y in range(0,H,10):
    s=rowsum[y:y+10].sum()
    if s>0: print(y, s)
