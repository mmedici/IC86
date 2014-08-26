"""
Functions for analyzing the
"""

from __future__ import print_function, division

import math

from icecube import dataclasses, finiteReco
from icecube.phys_services import I3Calculator as calc
from icecube.dataclasses import I3Constants


def om_partition(frame, output_name, options):
    """
    Partition the pulses.
    """

    # Initialize the RecoPulseSeriesMaps
    for partition in range(options['partitions']):
        key = output_name.format(partition)
        frame[key] = dataclasses.I3RecoPulseSeriesMap()

    # Get the pulse series
    pulse_series = frame[options['pulses_name']]
    if isinstance(pulse_series, dataclasses.I3RecoPulseSeriesMapMask):
        pulse_series = pulse_series.apply(frame)

    for dom, pulse_vector in pulse_series.items():

        # Find out which partition the pulse_vector is in
        partition_num = (dom.string + dom.om) % options['partitions']

        # Put it in every partition except the one where it goes
        for partition in range(options['partitions']):
            if partition != partition_num:
                key = output_name.format(partition)
                # Put it where it goes
                frame[key][dom] = pulse_vector


def dom_data(frame, reco_fit, options, extra):
    """

    Adds To Frame
    -------------
    TotalCharge : I3VectorDouble
    String : I3VectorDouble
    DistAboveEndpoint : I3VectorDouble
    ImpactParam : I3VectorDouble
    ImpactAngle : I3VectorDouble
    TimeResidual : I3VectorDouble
    RecoDistance : I3VectorDouble

    """

    n_ice_group = I3Constants.n_ice_group
    n_ice_phase = I3Constants.n_ice_phase

    IC_strings = [26, 27, 37, 46, 45, 35, 17, 18, 19, 28, 38, 47, 56, 55, 54, 44, 34, 25]
    DC_strings = [81, 82, 83, 84, 85, 86]

    reco_endpoint = frame['RecoEndpoint']

    # Get the pulse series
    pulse_series = frame[options['pulses_name']].apply(frame)

    # Get most energetic track
    if extra:
        mc_most_energetic = frame['MCTrueMostEnergetic']

    # Initialize
    frame['TotalCharge'] = dataclasses.I3VectorDouble()
    frame['String'] = dataclasses.I3VectorDouble()
    frame['OM'] = dataclasses.I3VectorDouble()
    frame['DistAboveEndpoint'] = dataclasses.I3VectorDouble()
    frame['ImpactParam'] = dataclasses.I3VectorDouble()
    frame['ImpactAngle'] = dataclasses.I3VectorDouble()
    frame['TimeResidual'] = dataclasses.I3VectorDouble()
    frame['RecoDistance'] = dataclasses.I3VectorDouble()
    if extra:
        frame['TrueDistance'] = dataclasses.I3VectorDouble()
        frame['DeltaDistance'] = dataclasses.I3VectorDouble()
        frame['NMuons'] = dataclasses.I3VectorDouble()

    # Find all doms above reconstructed z coord of endpoint and
    # within the specified distance interval of the track
    dom_geo = frame['I3Geometry'].omgeo.items()

    for dom, geo in dom_geo:  # (OMKey, I3OMGeo)

        # We want to get DOMs that are in the IC/DC strings and below the dust
        # layer.
        if (dom.string in IC_strings and dom.om >= 40) or (dom.string in DC_strings and dom.om >= 11):

            dom_position = geo.position
            partition_num = (dom.string + dom.om) % options['partitions']
            mpe = frame[reco_fit.format(partition_num)]  # MPEFit0...4

            # Find cherenkov distance from track to DOM
            reco_dist = calc.cherenkov_distance(mpe, dom_position, n_ice_group, n_ice_phase)
            if reco_dist < options['max_dist']:

                # Keep if track is below DOM
                clos_app_pos = calc.closest_approach_position(mpe, dom_position)
                if clos_app_pos.z < dom_position.z:

                    # Try cherenkov dist
                    cherenkov_pos = calc.cherenkov_position(mpe, dom_position, n_ice_group, n_ice_phase)
                    dist_above_endpoint = calc.distance_along_track(mpe, reco_endpoint) - calc.distance_along_track(mpe, cherenkov_pos)
                    if dist_above_endpoint > 0:

                        frame['RecoDistance'].append(reco_dist)
                        frame['DistAboveEndpoint'].append(dist_above_endpoint)

                        frame['String'].append(dom.string)
                        frame['OM'].append(dom.om)

                        perp_position = dataclasses.I3Position(dom_position.x, dom_position.y, clos_app_pos.z)
                        delta = perp_position - clos_app_pos
                        impact_param = delta.magnitude
                        frame['ImpactParam'].append(impact_param)

                        impact_angle = math.asin(impact_param / calc.closest_approach_distance(mpe, dom_position))
                        frame['ImpactAngle'].append(impact_angle)

                        # TotalCharge and TimeResidual
                        total_charge = 0

                        # If there are pulses, sum the charge of the ones with a
                        # time residual less than 1000 ns.
                        if dom in pulse_series.keys():
                            for pulse in pulse_series[dom]:
                                time_res = calc.time_residual(mpe, dom_position, pulse.time, n_ice_group, n_ice_phase)
                                if time_res < 1000:
                                    total_charge += pulse.charge
                                    frame['TimeResidual'].append(time_res)

                        frame['TotalCharge'].append(total_charge)

                        if extra:

                            true_dist = calc.cherenkov_distance(mc_most_energetic, dom_position, n_ice_group, n_ice_phase)
                            frame['TrueDistance'].append(true_dist)

                            delta_dist = true_dist - reco_dist
                            frame['DeltaDistance'].append(delta_dist)

                            # Iterate over the MMCTrackList and count how many
                            # muons have their Cherenkov position above the
                            # track endpoint but within 140 m of the track.
                            num_muons = 0
                            for track in frame['MMCTrackList']:
                                particle = track.particle
                                chpos = calc.cherenkov_position(particle, dom_position, n_ice_group, n_ice_phase)
                                chdist = calc.cherenkov_distance(particle, dom_position, n_ice_group, n_ice_phase)
                                z_endpoint = particle.shift_along_track(particle.length).z
                                if z_endpoint < chpos.z and chdist < options['max_dist']:
                                    num_muons += 1

                            frame['NMuons'].append(num_muons)
