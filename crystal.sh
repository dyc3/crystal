#!/bin/bash
cd /home/carson/Documents/code/crystal/
source .env/bin/activate
export DISPLAY=:0
python3 main.py --mode voice --log-level INFO