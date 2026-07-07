from PIL import Image
im=Image.open('docs/2019-2/pages/page-037.jpg')
im.crop((110,256,185,600)).resize((75*6,344*2)).save('scratchpad_own1.png')
im.crop((110,600,185,1120)).resize((75*6,520*2)).save('scratchpad_own2.png')
