#!/bin/bash

# requires mpy-cross build directory being in your PATH, e.g., by adding
# export PATH="/Users/marc/External/micropython/mpy-cross/build:$PATH"
# to your .zshrc/.bashrc:

mkdir -p build
for f in clock.py colors.py common.py frame.py paris.py solunar.py timing.py; do
    g="${f%.*}"
    mpy-cross ${f} -o build/${g}.mpy
done
