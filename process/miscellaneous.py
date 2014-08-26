"""
Miscellaneous functions that don't fit into one category.
"""

from __future__ import print_function, division

from icecube import dataclasses, finiteReco


def move_cut_variables(frame, direct_hits_name, hit_multiplicity_name, hit_statistics_name, fit_params_name):
    """
    Move cut variables calculated in the CommonVariables tray segments and the
    rlogl fit parameter for the provided fit into the top level of the frame.
    This is done so cuts.py can access these values directly.

    We want to use the 'C' time window for direct hits, ie. [-15 ns, +75 ns].

    This function requires the finiteReco module be imported from icecube to
    access the fit parameter object in the frame.

    Parameters
    ----------
    direct_hits_name : str
        The OutputI3DirectHitsValuesBaseName.

    hit_multiplicity_name : str
        The OutputI3HitMultiplicityValuesName.

    hit_statistics_name : str
        The OutputI3HitStatisticsValuesName.

    fit_params_name : str
        The fit parameters frame object name for the desired fit.

    Adds To Frame
    -------------
    NDirDoms : I3Double
    DirTrackLength : I3Double
    NHitDoms : I3Double
    COGX : I3Double
    COGY : I3Double
    COGZ : I3Double
    rlogl : I3Double
    """

    direct_hits = frame[direct_hits_name + 'C']
    frame['NDirDoms'] = dataclasses.I3Double(direct_hits.n_dir_doms)
    frame['DirTrackLength'] = dataclasses.I3Double(direct_hits.dir_track_length)

    hit_multiplicity = frame[hit_multiplicity_name]
    frame['NHitDoms'] = dataclasses.I3Double(hit_multiplicity.n_hit_doms)

    hit_statistics = frame[hit_statistics_name]
    frame['COGX'] = dataclasses.I3Double(hit_statistics.cog.x)
    frame['COGY'] = dataclasses.I3Double(hit_statistics.cog.y)
    frame['COGZ'] = dataclasses.I3Double(hit_statistics.cog.z)

    fit_params = frame[fit_params_name]
    frame['rlogl'] = dataclasses.I3Double(fit_params.rlogl)


def finite_reco_param(frame, finite_reco_name):
    """
    TODO document this.

    Adds To Frame
    -------------
    FRStopLLHRatio : I3Double

    """
    if finite_reco_name in frame:
        llh = frame[finite_reco_name]
        llh_ratio = dataclasses.I3Double(llh.LLHStoppingTrack - llh.LLHInfTrack)
        frame['FRStopLLHRatio'] = llh_ratio


def count_hits(frame, pulses_name):
    """
    TODO document this.

    Adds To Frame
    -------------
    ICNHits : I3Double

    ICAnalysisHits : I3Double

    DCAnalysisHits : I3Double

    """
    IC_strings = [36, 26, 27, 35, 37, 45, 46, 17, 18, 19, 28, 38, 47, 56, 55, 54, 44, 34, 25]
    DC_strings = [81, 82, 83, 84, 85, 86]

    IC_num_hits = 0
    ICLC_counter = 0
    ICLC_cut_counter = 0
    DCLC_counter = 0
    IC_analysis_hits = 0
    DC_analysis_hits = 0

    pulse_series = frame[pulses_name].apply(frame)
    raw_data = frame['InIceRawData']

    for dom in pulse_series.keys():
        if dom.string in DC_strings:
            if dom.om >= 11:
                DC_analysis_hits += 1
            if raw_data[dom][0].lc_bit:
                DCLC_counter += 1
        else:  # It's not in DC_strings
            if raw_data[dom][0].lc_bit:
                ICLC_counter += 1
            if dom.string not in IC_strings:
                IC_num_hits += 1  # The number of hits
                if raw_data[dom][0].lc_bit:
                    ICLC_cut_counter += 1
            elif dom.string in IC_strings and dom.om >= 40:
                IC_analysis_hits += 1

    frame['ICNHits'] = dataclasses.I3Double(IC_num_hits)
    frame['NICLC'] = dataclasses.I3Double(ICLC_counter)  # TODO rename all these things so they are more consistent.
    frame['ICLCCut'] = dataclasses.I3Double(ICLC_cut_counter)
    frame['NDCLC'] = dataclasses.I3Double(DCLC_counter)
    frame['ICAnalysisHits'] = dataclasses.I3Double(IC_analysis_hits)
    frame['DCAnalysisHits'] = dataclasses.I3Double(DC_analysis_hits)


def reco_endpoint(frame, endpoint_fit):
    """
    Calculate the reconstructed endpoint of the event.

    Parameters
    ----------
    endpoint_fit : str
        The fit used to calculate the endpoint.

    Adds To Frame
    -------------
    RecoEndpoint : I3Position
        The reconstructed endpoint of the event.
    """

    reco_fit = frame[endpoint_fit]
    endpoint = reco_fit.shift_along_track(reco_fit.length)
    frame['RecoEndpoint'] = endpoint


def reco_endpoint_z(frame):
    """
    Move the z coordinate of the reconstructed endpoint into the top level of
    the frame. This is done so cuts.py can access it directly.

    Adds To Frame
    -------------
    RecoEndpointZ : I3Double
        z coordinate of the reconstructed endpoint.
    """

    reco_z = frame['RecoEndpoint'].z
    frame['RecoEndpointZ'] = dataclasses.I3Double(reco_z)
