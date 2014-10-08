"""
Functions that analyze the geometry of events relative to the detector.

All these functions rely heavily on geometry.py, which does the heavy lifting.
"""

from __future__ import print_function, division

from icecube import dataclasses
from I3Tray import OMKey

from geometry import point_to_polygon_dist, point_in_polygon


def get_coordinates(omgeo, strings):
    """
    Return a list of the (x, y) coordinates of the given strings.

    Parameters
    ----------
    omgeo : I3OMGeoMap[OMKey] -> I3OMGeo
        Geometry of the DOMs.

    strings: list of ints
        The strings to get the coordinates of.

    Returns
    -------
    list of tuples
        The (x, y) coordinates of each string.
    """

    coords = []
    for string in strings:
        om = OMKey(string, 1)  # Use first DOM on the string.
        om_x = omgeo[om].position.x
        om_y = omgeo[om].position.y
        point = (om_x, om_y)

        coords.append(point)

    return coords


def calc_dist_to_border(frame):
    """
    Calculate the signed minimum distance of the reconsructed endpoint to the
    detector border.

    Events inside the detector are given positive distances, and events outside
    negative.

    Adds To Frame
    -------------
    DistToBorder : I3Double
        The signed minimum distance of the reconstructed endpoint to the detector
        border.
    """

    reco_endpoint = frame['RecoEndpoint']
    endpoint = (reco_endpoint.x, reco_endpoint.y)

    omgeo = frame['I3Geometry'].omgeo
    border_strings = [1, 2, 3, 4, 5, 6, 13, 21, 30, 40, 50, 59, 67, 74, 73, 72, 78, 77, 76, 75, 68, 60, 51, 41, 31, 22, 14, 7]  # For IC86

    # Get the (x, y) coordinates of the border doms.
    detector_border = get_coordinates(omgeo, border_strings)

    dist = point_to_polygon_dist(endpoint, detector_border)

    inside = point_in_polygon(endpoint, detector_border)

    # Endpoints outside detector get negative distances.
    if not inside:
        dist = -dist

    frame['DistToBorder'] = dataclasses.I3Double(dist)
