#!/bin/bash

# Path to the GCD file
gcd=/data/sim/IceCube/2011/filtered/level2/CORSIKA-in-ice/10668/00000-00999/GeoCalibDetectorStatus_IC86.55697_corrected_V2.i3.gz
# Path to the data file(s). This can be just one data file or a globbed expression.
datafiles=/data/sim/IceCube/2011/filtered/level2/CORSIKA-in-ice/10668/00000-00999/Level2_IC86.2011_corsika.010668.000000.i3.bz2
# Directory where output files are saved
outdir=/scratch

for data in $datafiles
do
    ofile=$outdir/$(basename $data)
    # Replace /home/jgarber with the appropriate path on your machine.
    python /home/jgarber/IC86/process/process.py -e $gcd $data $ofile  # extra processing turned on
done
