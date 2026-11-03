#!/usr/bin/env bash
# Download the Tesseract models this project compares (Arabic + English, fast and best).
set -euo pipefail
cd "$(dirname "$0")/.."
for v in fast best; do
  mkdir -p "tessdata/$v"
  for l in ara eng; do
    f="tessdata/$v/$l.traineddata"
    [ -s "$f" ] || curl -sSfL -o "$f" "https://github.com/tesseract-ocr/tessdata_$v/raw/main/$l.traineddata"
  done
done
echo "tessdata ready"
