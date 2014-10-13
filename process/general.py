"""
General functions that don't fit into one category.
"""

from __future__ import print_function, division

from icecube import dataclasses, finiteReco


def get_truth_muon(frame):
    """
    Count the number of in ice muons and get the most energetic one.
    """
    tree = frame['I3MCTree']

    muons = []
    for particle in tree.in_ice:
        if particle.type_string in ('MuPlus', 'MuMinus'):
            muons.append(particle)

    frame['NumInIceMuons'] = dataclasses.I3Double(len(muons))

    max_energy_muon = muons[0]
    for muon in muons:
        if muon.energy > max_energy_muon.energy:
            max_energy_muon = muon

    frame['TruthMuon'] = max_energy_muon


def truth_endpoint(frame):
    muon = frame['TruthMuon']
    truth_endpoint = muon.shift_along_track(muon.length)
    frame['TruthEndpoint'] = truth_endpoint


def count_hits(frame, pulses_name):
    """
    TODO document this.

    Adds To Frame
    -------------
    ICAnalysisHits : I3Double
        The number of hits within the IC analysis region.

    DCAnalysisHits : I3Double
        The number of hits within the DC analysis region.

    ICNHits : I3Double
        The number of hits outside the IC analysis region.

    DCNHits : I3Double
        The number of hits outside the DC analysis region.
    """

    IC_strings = [26, 27, 37, 46, 45, 35, 17, 18, 19, 28, 38, 47, 56, 55, 54, 44, 34, 25]
    DC_strings = [81, 82, 83, 84, 85, 86]

    IC_analysis_hits = 0
    DC_analysis_hits = 0
    IC_nhits = 0
    DC_nhits = 0

    pulse_series = frame[pulses_name].apply(frame)

    for dom in pulse_series.keys():
        if dom.string in IC_strings and dom.om >= 40:
            IC_analysis_hits += 1
        if dom.string in DC_strings and dom.om >= 11:
            DC_analysis_hits += 1

        if dom.string not in [36, 79, 80] + DC_strings + IC_strings:
            IC_nhits += 1
        if dom.string not in [36, 79, 80] + DC_strings:
            DC_nhits += 1

    frame['ICAnalysisHits'] = dataclasses.I3Double(IC_analysis_hits)
    frame['DCAnalysisHits'] = dataclasses.I3Double(DC_analysis_hits)
    frame['ICNHits'] = dataclasses.I3Double(IC_nhits)
    frame['DCNHits'] = dataclasses.I3Double(DC_nhits)


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


def move_cut_variables(frame, direct_hits_name, fit_params_name):
    """
    Move NDirDoms calculated in direct_hits, the rlogl fit parameter for the
    provided fit, and the z coordinate of the reconstructed endpoint into the
    top level of the frame. This is done so cuts.py can access these values
    directly.

    We want to use the 'C' time window for direct hits, ie. [-15 ns, +75 ns].

    This function requires the finiteReco module be imported from icecube to
    access the fit parameter object in the frame.

    Parameters
    ----------
    direct_hits_name : str
        The OutputI3DirectHitsValuesBaseName.

    fit_params_name : str
        The fit parameters frame object name for the desired fit.

    Adds To Frame
    -------------
    NDirDoms : I3Double
    rlogl : I3Double
    RecoEndpointZ : I3Double
    """

    direct_hits = frame[direct_hits_name + 'C']
    frame['NDirDoms'] = dataclasses.I3Double(direct_hits.n_dir_doms)

    fit_params = frame[fit_params_name]
    frame['rlogl'] = dataclasses.I3Double(fit_params.rlogl)

    reco_z = frame['RecoEndpoint'].z
    frame['RecoEndpointZ'] = dataclasses.I3Double(reco_z)
