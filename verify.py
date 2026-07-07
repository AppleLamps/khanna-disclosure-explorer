from PIL import Image
im=Image.open('docs/2019-2/pages/page-037.jpg')
for name,y0,y1 in [("SNAP_r36",672,687),("STONE_r57",924,939),("STRYKER_r59",939,952),("TARGA_r69",1056,1071)]:
    c=im.crop((740,y0,1500,y1)).resize((760*2,(y1-y0)*6))
    c.save(f'scratchpad_{name}.png')
    print("saved",name)
