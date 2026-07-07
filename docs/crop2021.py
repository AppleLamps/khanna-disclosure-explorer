import os, glob
from concurrent.futures import ProcessPoolExecutor
from PIL import Image
FRAC = 0.54
def crop_page(path):
    d = os.path.dirname(os.path.dirname(path)); base = os.path.basename(path).replace(".png","")
    os.makedirs(f"{d}/quads", exist_ok=True)
    im = Image.open(path); W,H = im.size; cw,ch = int(W*FRAC), int(H*FRAC)
    for q,box in {"TL":(0,0,cw,ch),"TR":(W-cw,0,W,ch),"BL":(0,H-ch,cw,H),"BR":(W-cw,H-ch,W,H)}.items():
        im.crop(box).convert("L").save(f"{d}/quads/{base}-{q}.jpg", quality=85)
if __name__ == "__main__":
    pages = sorted(glob.glob("docs/2021-*/hires/*.png"))
    with ProcessPoolExecutor(max_workers=8) as ex: list(ex.map(crop_page, pages))
    print("CROP2021_DONE", len(pages))
