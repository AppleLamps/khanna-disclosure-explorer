from PIL import Image
im=Image.open('docs/2019-2/pages/page-037.jpg')
im.crop((180,196,620,214)).resize((440*3,18*4)).save('scratchpad_group037.png')
# a few name rows for spelling
im.crop((175,256,700,270)).resize((525*2,14*5)).save('scratchpad_n1.png')      # row1 RICHLAND
im.crop((175,388,700,400)).resize((525*2,12*5)).save('scratchpad_n12.png')     # row12 S O CONSERVANCY
im.crop((175,400,700,410)).resize((525*2,10*5)).save('scratchpad_n13.png')     # row13 S&P GLOBAL area
im.crop((175,258,420,600)).resize((245*4,342*2)).save('scratchpad_owner.png')  # owner column rows1-30
