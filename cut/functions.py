"""
Functions used in cut.py.
"""

import numpy as np
import tables

from icecube import icetray, dataclasses, dataio


def make_event_cuts(frame, event_cuts):
    """
    Cut out the frames that do not pass the event cuts.

    Parameters
    ----------
    event_cuts : dict[str] -> tuple
        Contains the event cuts. The keys are the names of the objects within
        the frame, and the values are tuples containing the information on the
        cut to make. For example, event_cuts['NDirDoms'] = ('greater than', 5)
        means we only keep frames with an 'NDirDoms' that is greater than 5. Easy.

    Returns
    -------
    bool
        Indicates if the frame passed all the event cuts.
    """

    for key, (function, value) in event_cuts.items():
        # Get the data for making the cut.
        data = frame[key].value

        # Make the appropriate cut.
        pass_cut = function(data, value)

        # If it didn't pass the cut, return False.
        if not pass_cut:
            return False

    # It passed all the cuts, so return True.
    return True


def make_dom_cuts(frame, dom_cuts, dom_keys):
    """
    Cut out the data for the DOMs that do not pass the dom cuts, then split
    apart the data that did pass into IC/DC.

    Parameters
    ----------
    dom_cuts : dict[str] -> tuple
        Contains the information about the dom cuts. The layout of this
        dictionary is the same as event_cuts. Ie.
        dom_cuts['DistAboveEndpoint'] = ('greater than', 100)
        means only keep the dom data with a 'DistAboveEndpoint' that is greater
        than 100.

    dom_keys : list of str
        The keys of the dom data to make a cut on. These are the keys that are
        written to the HDF5 file (it doesn't make sense to do a cut on data that
        won't be saved).

    Adds To Frame
    -------------
    NameOfDOMKeyIC, NameOfDOMKeyDC : I3VectorDouble
        The cut DOM data split apart into IC and DC. This is done for all the
        keys in dom_keys.
    """

    # pass_cut is a boolean array that records which data passes the
    # dom cuts. We need to initialize it to an array the same length as the dom
    # data (in this case using 'String', but it doesn't matter). We need to
    # explicitly say "dtype=bool" in the case that len(frame['String']) == 0.
    pass_cut = np.array([True] * len(frame['String']), dtype=bool)

    # Iterate over the data and make the cuts.
    for key, (function, value) in dom_cuts.items():
        data = np.array(frame[key])

        # Update pass_cut for the events that pass the cut.
        pass_cut &= function(data, value)

    # Iterate over the dom keys we want to keep and make the cut.
    for key in dom_keys:

        # Get the data.
        data = np.array(frame[key])

        # Make the cut.
        pass_cut_data = data[pass_cut]

        # Put it back in the frame.
        frame[key + 'Cut'] = dataclasses.I3VectorDouble(pass_cut_data)


def write_cut_metadata(ofile, event_cuts, dom_cuts):
    """
    Write the cuts to the HDF5 file as metadata.

    In PyTables lingo, these are called "attributes". You can recover them later
    by opening the file and getting

    infile.root._v_attrs.event_cuts
    infile.root._v_attrs.dom_cuts

    Parameters
    ----------
    ofile : str
        Path to the output HDF5 file.

    event_cuts : dict[str] -> tuple
        Contains the event cuts. The keys are the names of the objects within
        the frame, and the values are tuples containing the information on the
        cut to make. For example, event_cuts['NDirDoms'] = ('greater than', 5)
        means we only keep frames with an 'NDirDoms' that is greater than 5. Easy.

    dom_cuts : dict[str] -> tuple
        Contains the information about the dom cuts. The layout of this
        dictionary is the same as event_cuts. Ie.
        dom_cuts['DistAboveEndpoint'] = ('greater than', 100)
        means only keep the dom data with a 'DistAboveEndpoint' that is greater
        than 100.
    """

    infile = tables.open_file(ofile, 'a')

    infile.root._v_attrs.event_cuts = event_cuts
    infile.root._v_attrs.dom_cuts = dom_cuts

    infile.close()
