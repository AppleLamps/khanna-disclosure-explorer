from PIL import Image
import numpy as np
im=Image.open('docs/2019-2/pages/page-037.jpg').convert('L')
a=np.array(im)
c=a[196:214,180:420]
# upscale with contrast
from PIL import Image as I
img=I.fromarray(c).resize((240*5,18*6), I.LANCZOS)
img.save('scratchpad_group037b.png')
