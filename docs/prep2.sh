#!/bin/zsh
set -e
cd /Users/multivac/Code/khanna
for f in docs/src/*.pdf; do
  doc=$(basename $f .pdf)
  mkdir -p docs/$doc/pages docs/$doc/hires docs/$doc/tess docs/$doc/text
  pdftoppm -jpeg -r 150 -jpegopt quality=80 $f docs/$doc/pages/page
  pdftoppm -png -r 300 -gray $f docs/$doc/hires/page
done
echo "rendered"
ls docs/*/pages/*.jpg docs/*/hires/*.png | xargs -n 1 -P 8 sips -r 270 >/dev/null 2>&1
echo "rotated"
python3 docs/crop2.py
ls docs/*/hires/*.png | xargs -I {} -P 8 sh -c 'd=$(dirname $(dirname {})); b=$(basename {} .png); tesseract {} $d/tess/$b 2>/dev/null'
echo "PREP2_DONE $(ls docs/*/tess/*.txt | wc -l)"
