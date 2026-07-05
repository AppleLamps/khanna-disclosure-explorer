#!/bin/zsh
# Wait for hires rendering to finish, then rotate, crop quadrants, tesseract.
set -e
cd /Users/multivac/Code/khanna

# wait for all 333 hires pages + pdftoppm exit
while true; do
  n=$(ls ocr/hires 2>/dev/null | wc -l | tr -d ' ')
  if [ "$n" = "333" ] && ! pgrep -f "pdftoppm -png" >/dev/null; then break; fi
  sleep 5
done
echo "hires ready"

mkdir -p ocr/quads ocr/tess

# rotate hires 270 in place (parallel batches of 8)
ls ocr/hires/*.png | xargs -n 1 -P 8 sips -r 270 >/dev/null 2>&1
echo "rotated"

# quadrant crops with overlap -> jpeg
crop_one() {
  f=$1
  base=$(basename $f .png)
  read W H <<< $(sips -g pixelWidth -g pixelHeight $f | awk '/pixelWidth/{w=$2}/pixelHeight/{h=$2}END{print w, h}')
  cw=$(( W * 54 / 100 )); ch=$(( H * 54 / 100 ))
  ox=$(( W - cw )); oy=$(( H - ch ))
  for q in TL TR BL BR; do
    case $q in
      TL) x=0;   y=0   ;;
      TR) x=$ox; y=0   ;;
      BL) x=0;   y=$oy ;;
      BR) x=$ox; y=$oy ;;
    esac
    sips -c $ch $cw --cropOffset $y $x -s format jpeg -s formatOptions 85 $f --out ocr/quads/$base-$q.jpg >/dev/null 2>&1
  done
}
export -f crop_one 2>/dev/null || true
for f in ocr/hires/*.png; do crop_one $f & ; while [ $(jobs -r | wc -l) -ge 8 ]; do wait -n 2>/dev/null || sleep 0.2; done; done
wait
echo "quads: $(ls ocr/quads | wc -l)"

# tesseract baseline on rotated hires
ls ocr/hires/*.png | xargs -I {} -P 8 sh -c 'b=$(basename {} .png); tesseract {} ocr/tess/$b 2>/dev/null'
echo "tess: $(ls ocr/tess | wc -l)"
echo "PREP_ALL_DONE"
