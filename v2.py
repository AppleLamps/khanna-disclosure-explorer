from PIL import Image
im=Image.open('docs/2019-2/pages/page-037.jpg')
c=im.crop((740,901,1500,914)).resize((760*2,13*6)); c.save('scratchpad_STERI_r55.png')
