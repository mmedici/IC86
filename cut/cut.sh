#!/bin/bash

# Path to the data file(s) to make cuts on. This should be an output file from process.sh. It can  be a globbed expression, in which case all the files will be cut and saved under one HDF5 file.
datafiles=/data/user/jgarber/10668/*.i3.bz2
# Name of the HDF5 file to save the data as.
ofile=/data/user/jgarber/10668/10668_cut.h5

python /home/jgarber/IC86/cut/cut.py -d $datafiles -o $ofile
