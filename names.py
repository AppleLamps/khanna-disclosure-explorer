from PIL import Image
import sys
p=sys.argv[1]
im=Image.open(f'docs/2019-2/pages/page-{p}.jpg')
# name column x175-720; split top/bottom
im.crop((175,252,720,690)).resize((545*2,438*2)).save(f'scratchpad_{p}_top.png')
im.crop((175,690,720,1130)).resize((545*2,440*2)).save(f'scratchpad_{p}_bot.png')
