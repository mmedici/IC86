#!/bin/bash

# Path to the GCD file
gcd=/data/sim/IceCube/2011/filtered/level2/CORSIKA-in-ice/10915/00000-00999/GeoCalibDetectorStatus_IC86.55697_corrected_V2.i3.gz
# Path to the data file(s). This can be just one data file or a globbed expression.
datafiles=/data/sim/IceCube/2011/filtered/level2/CORSIKA-in-ice/10915/00000-00999/Level2_IC86.2011_corsika.010915.000000.i3.bz2
# Directory where output files are saved
outdir=/scratch/jgarber

for data in $datafiles
do
    ofile=$outdir/$(basename $data)
    python /home/jgarber/IC86/process/process.py $gcd $data $ofile -s
done
