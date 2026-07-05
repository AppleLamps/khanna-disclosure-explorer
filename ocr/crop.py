#!/usr/bin/env python3
"""Cut each rotated hires page into 4 overlapping quadrant crops."""
import os, sys, glob
from concurrent.futures import ProcessPoolExecutor
from PIL import Image

SRC = "ocr/hires"
DST = "ocr/quads"
FRAC = 0.54  # each quadrant covers 54% of each dimension -> 8% overlap

def crop_page(path):
    base = os.path.basename(path).replace(".png", "")
    im = Image.open(path)
    W, H = im.size
    cw, ch = int(W * FRAC), int(H * FRAC)
    boxes = {
        "TL": (0, 0, cw, ch),
        "TR": (W - cw, 0, W, ch),
        "BL": (0, H - ch, cw, H),
        "BR": (W - cw, H - ch, W, H),
    }
    for q, box in boxes.items():
        im.crop(box).convert("L").save(f"{DST}/{base}-{q}.jpg", quality=85)
    return base

if __name__ == "__main__":
    os.makedirs(DST, exist_ok=True)
    pages = sorted(glob.glob(f"{SRC}/*.png"))
    with ProcessPoolExecutor(max_workers=8) as ex:
        for i, b in enumerate(ex.map(crop_page, pages)):
            if (i + 1) % 50 == 0:
                print(f"{i+1}/{len(pages)}", flush=True)
    print("CROP_DONE", len(pages))
