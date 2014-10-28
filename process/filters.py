"""
Functions for filtering out frames.

These are the base "cuts": they are always the same. The variable cuts
(the ones you want to fiddle with), are done later in the cuts.py script
(see the 'event_cuts' and 'dom_cuts' dictionaries in cut_options_example.py).
"""

from __future__ import print_function, division

import math

from icecube import dataclasses


def in_ice(frame):
    """
    Check that sub_event_stream == 'in_ice'.
    """
    event_header = frame['I3EventHeader']
    return event_header.sub_event_stream == 'in_ice'


def min_bias(frame):
    """
    Check that condition_passed and prescale_passed for FilterMinBias_11 are
    both True.
    """
    filter_mask = frame['FilterMask']
    filter_min_bias = filter_mask['FilterMinBias_11']
    return filter_min_bias.condition_passed and filter_min_bias.prescale_passed


def SMT8(frame):
    """
    Check that the length of TWOfflinePulsesHLC >= 8.
    """
    pulse_series = frame['TWOfflinePulsesHLC'].apply(frame)
    return len(pulse_series) >= 8


def MPEFit(frame):
    """
    Check that the fit_status of MPEFit is OK and that the zenith is
    between 40 and 70 degrees.
    """
    mpe = frame['MPEFit']
    angle = math.degrees(mpe.dir.zenith)
    return mpe.fit_status == dataclasses.I3Particle.OK and 40 < angle < 70


def InIceSMTTriggered(frame):
    """
    Check that InIceSMTTriggered is True.
    """
    return frame['InIceSMTTriggered'].value
