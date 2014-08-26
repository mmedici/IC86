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

    for key, cut in event_cuts.items():
        # Get the data for making the cut.
        data = frame[key].value

        # Make the appropriate cut.
        if cut[0] == 'less than':
            pass_cut = data < cut[1]
        elif cut[0] == 'greater than':
            pass_cut = data > cut[1]

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
    for key, cut in dom_cuts.items():
        data = np.array(frame[key])
        if cut[0] == 'less than':
            pass_cut_temp = data < cut[1]
        elif cut[0] == 'greater than':
            pass_cut_temp = data > cut[1]

        # Update pass_cut for the events that passed the last cut.
        pass_cut &= pass_cut_temp

    # Get the string numbers for the data that passed the cut.
    string = np.array(frame['String'])
    pass_cut_string = string[pass_cut]

    # Iterate over the dom keys we want to keep and make the cut.
    for key in dom_keys:

        if key == 'TimeResidual':  # We don't do a cut on TimeResidual
            continue

        # Get the data.
        data = np.array(frame[key])

        # Make the cut.
        pass_cut_data = data[pass_cut]

        # Split it apart into IC and DC
        data_IC, data_DC = IC_DC_split(pass_cut_data, pass_cut_string)

        # Put it back in the frame.
        frame[key + 'IC'] = dataclasses.I3VectorDouble(data_IC)
        frame[key + 'DC'] = dataclasses.I3VectorDouble(data_DC)


def IC_DC_split(data, string):
    """
    Split the data apart into data for IC strings and data for DC strings.

    Parameters
    ----------
    data : np.ndarray of float
        The data array.

    string : np.ndarray of int
        The corresponding string numbers. The string numbers line up with the
        data (ie. the string number for data[0] is string[0], etc.)

    Returns
    -------
    data_IC, data_DC : np.ndarray
        The data for IC and DC.
    """
    IC_strings = [26, 27, 37, 46, 45, 35, 17, 18, 19, 28, 38, 47, 56, 55, 54, 44, 34, 25]
    DC_strings = [81, 82, 83, 84, 85, 86]

    IC_cut = np.in1d(string, IC_strings)
    DC_cut = np.in1d(string, DC_strings)

    data_IC = data[IC_cut]
    data_DC = data[DC_cut]

    return data_IC, data_DC


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
