"""
Functions that do additional processing for the Monte Carlo data of simulated
datasets. These are only used when the '--extra' flag is passed to process.py.
"""

from __future__ import print_function, division

from icecube import dataclasses, simclasses


def mc_tracks(frame):
    """
    Move the tracks in MMCTrackList into the top level of the frame.
    I'm not sure if we need to do this, so I won't bother with docs right now.
    """
    mmc = frame['MMCTrackList']  # simclasses
    for index, track in enumerate(mmc):
        key = 'MCTruePart{}'.format(index)
        frame[key] = track.particle


def total_ec(frame):
    mmc = frame['MMCTrackList']
    ec = sum(track.Ec for track in mmc if track.Ec > 0)
    frame['TotalEc'] = dataclasses.I3Double(ec)


def mc_most_energetic(frame):
    """
    Get the most energetic in ice particle from the I3MCTree.

    Adds To Frame
    -------------
    MCTrueMostEnergetic : I3Particle
        The most energetic in ice particle in the I3MCTree.
    """

    tree = frame['I3MCTree']
    particle = tree.most_energetic_in_ice
    frame['MCTrueMostEnergetic'] = particle


def primary_energy(frame):
    tree = frame['I3MCTree']
    particle = frame['MCTrueMostEnergetic']
    primary_energy = tree.get_primary(particle).energy
    frame['PrimaryEnergy'] = dataclasses.I3Double(primary_energy)
