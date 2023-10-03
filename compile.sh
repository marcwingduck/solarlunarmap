#!/bin/bash

# requires mpy-cross build directory being in your PATH, e.g., by adding
# export PATH="/Users/marc/External/micropython/mpy-cross/build:$PATH"
# to your .zshrc/.bashrc:

for f in colors.py common.py frame.py paris.py solunar.py timing.py; do mpy-cross ${f}; done
