#!/bin/bash

# Path to the data file(s) to make cuts on. These should be output processing files. It can be a globbed expression, in which case all the files will be cut and saved under one HDF5 file.
datafiles=/data/user/jgarber/10668/*.i3.bz2
# Name of the HDF5 file to save the data as.
ofile=/data/user/jgarber/10668/10668_cut.h5

# We need to add the current directory (or whatever directory contains cut_options.py) to the PYTHONPATH so cut.py can find it
PYTHONPATH=$(dirname $0):$PYTHONPATH python /home/jgarber/IC86/cut/cut.py -d $datafiles -o $ofile
