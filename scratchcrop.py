from PIL import Image
im=Image.open('docs/2019-2/pages/page-037.jpg')
# crop header + first ~12 rows, columns None..col5
c=im.crop((690,160,1030,420)).resize((340*4,260*4))
c.save('scratchpad_zoom037.png')
print("saved", c.size)
