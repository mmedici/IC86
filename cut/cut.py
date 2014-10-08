#!/usr/bin/env python

"""
Script for making event and DOM cuts.
"""

from __future__ import print_function, division  # 2to3

import argparse
import math

import I3Tray
from icecube import icetray, dataclasses, dataio
from icecube.hdfwriter import I3HDFTableService
from icecube.tableio import I3TableWriter

from functions import make_event_cuts, make_dom_cuts, write_cut_metadata

# The event cuts to make. Change these as much as you like.
event_cuts = {}
event_cuts['NDirDoms'] = ('greater than', 5)
event_cuts['rlogl'] = ('less than', 10)
event_cuts['ICNHits'] = ('less than', 20)
event_cuts['RecoEndpointZ'] = ('greater than', -400)
event_cuts['DistToBorder'] = ('greater than', 50)
event_cuts['ICAnalysisHits'] = ('greater than', 0)

# The dom cuts to make. Change these freely.
dom_cuts = {}
dom_cuts['ImpactAngle'] = ('less than', math.pi / 2)  # Must be radians
dom_cuts['DistAboveEndpoint'] = ('greater than', 100)

# The keys containing the per DOM data
dom_keys = ['TotalCharge', 'String', 'OM', 'DistAboveEndpoint', 'ImpactAngle', 'RecoDistance']

def main():

    parser = argparse.ArgumentParser(description='script for making event and DOM cuts')
    parser.add_argument('-d', '--datafiles', help='data files to make the cuts on',
                        nargs='+', required=True)
    parser.add_argument('-o', '--ofile', help='name of output HDF5 file',
                        required=True)
    args = parser.parse_args()

    tray = I3Tray.I3Tray()

    tray.AddModule('I3Reader', 'I3Reader',
                   Filenamelist=args.datafiles)

    # Cut out the frames that do not pass the event cuts.
    tray.AddModule(make_event_cuts, 'make_event_cuts',
                   event_cuts=event_cuts)

    # The remaining frames pass all the event cuts. Now go into the
    # dom data of each frame and make the dom cuts.
    tray.AddModule(make_dom_cuts, 'make_dom_cuts',
                   dom_cuts=dom_cuts,
                   dom_keys=dom_keys)

    # Make a new HDF5 file
    hdf5 = I3HDFTableService(args.ofile)

    tray.AddModule(I3TableWriter, 'I3TableWriter',
                   TableService=hdf5,
                   BookEverything=True,
                   SubEventStreams=['in_ice'])

    tray.Execute()
    tray.Finish()

    # Now write the cuts we made to the HDF5 as metadata (so we know for later).
    write_cut_metadata(args.ofile, event_cuts, dom_cuts)


if __name__ == '__main__':
    main()
