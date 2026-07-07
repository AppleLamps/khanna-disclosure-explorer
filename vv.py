from PIL import Image
im=Image.open('docs/2019-2/pages/page-038.jpg')
# rows 54-56 approx y. row height ~11.5, row1 at y256. row54 ~ 256+53*11.6=871
im.crop((175,866,760,905)).resize((585*2,39*5)).save('scratchpad_v5456.png')
# row33 U S DOLLAR value region, row33 y ~256+32*11.6=627
im.crop((640,624,1120,637)).resize((480*2,13*6)).save('scratchpad_usd.png')
# row47 full width to see name extent & EIF
im.crop((175,786,1120,800)).resize((945,14*6)).save('scratchpad_r47.png')
