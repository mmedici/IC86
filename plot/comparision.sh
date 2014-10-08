#!/bin/bash

# Path to first dataset (from cutting script). Must be HDF5 file.
data1=/data/user/jgarber/Level2a_IC79_corsika.008316.000000_cut.h5
# Label for first dataset when plotting
label1=MC0
# Path to second dataset (from cutting script). Must be HDF5 file.
data2=/data/user/jgarber/Level2a_IC79_corsika.008316.000001_cut.h5
# Label for second dataset when plotting
label2=MC1
# Output director to save plots.
outdir=/data/user/jgarber

python /home/jgarber/IC86/plot/plot.py $data1 $label1 $data2 $label2 $outdir
