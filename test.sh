#!/bin/bash

rm -r tests/__pycache__
python -m unittest -c tests/*
