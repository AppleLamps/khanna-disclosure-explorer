from PIL import Image
import numpy as np
im=Image.open('docs/2019-2/pages/page-040.jpg').convert('L')
a=np.array(im); H,W=a.shape; b=(a<180).astype(np.uint8)
# find header text rows in x>900 region near top (y 240-285)
for y in range(230,290):
    s=b[y,900:1500].sum()
    if s>3: print(y, int(s))
