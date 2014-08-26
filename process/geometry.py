"""
Functions for simple problems in 2D computational geometry.

The functions in this module are independent of the IceCube framework, so a few
functions are needed to extract the necessary data from the I3 frames to pass
along to these ones. Those functions are contain in geoanalysis.py.
"""
from __future__ import print_function, division  # 2to3

import numpy as np
from numpy import linalg


def point_to_seg_dist(point, seg_p1, seg_p2):
    """
    Calculate the shortest distance from a point to a line segment.

    Parameters
    ----------
    point : tuple
        The (x, y) coordinates of the point.

    seg_p1 : tuple
        The (x, y) coordinates of the first endpoint of the line segment.

    seg_p2 : tuple
        The (x, y) coordinates of the second endpoint of the line segment.

    Returns
    -------
    float
        Shortest distance of point to line segment.

    Examples
    --------
    >>> p = (0, 1)
    >>> p1 = (0, 0)
    >>> p2 = (1, 1)
    >>> point_to_seg_dist(p, p1, p2)
    0.70710678118654757
    """

    # Vectorize the points.
    point = np.array(point)
    seg_p1 = np.array(seg_p1)
    seg_p2 = np.array(seg_p2)

    seg_vector = seg_p2 - seg_p1  # Line segment vector
    point_vector = point - seg_p1  # Vector from point to seg_p1

    length_sqrd = linalg.norm(seg_vector) ** 2  # Squared length of line segment.
    if length_sqrd == 0:  # In this case, seg_p1 == seg_p2
        # Just return the distance from point to seg_p1.
        return linalg.norm(point_vector)

    # We can parameterize the line L defined by the line segment as
    # L = seg_p1 + t * seg_vector.

    # The parameter for the projection of the point_vector onto the line L.
    t = np.dot(seg_vector, point_vector) / length_sqrd

    if t <= 0:  # Projection lies beyond seg_p1
        closest_point = seg_p1
    elif t >= 1:  # Projection lies beyond seg_p2
        closest_point = seg_p2
    else:  # Projection lies on the segment
        closest_point = seg_p1 + t * seg_vector  # Projection onto segment

    distance = linalg.norm(closest_point - point)

    return distance


def point_to_polygon_dist(point, polygon):
    """
    Calculate the shortest distance from a point to a polygon.

    Parameters
    ----------
    point : tuple
        The (x, y) coordinates of the point.

    polygon: list of tuples
        The (x, y) coordinates of the vertices of the polygon. These vertices
        must be "in order", meaning there is a line connecting polygon[0] to
        polygon[1], and then polygon[1] to polygon[2], etc.

        Note: Do not add the first point of the list to the end (to reflect
        the cyclic nature of the polygon); it is taken care of in the
        algorithm.

    Returns
    -------
    float
        The shortest distance to the polygon.

    Examples
    --------
    >>> p = (0.5, 0.5)
    >>> poly = [(0, 0), (0, 1), (1, 1), (1, 0)]  # Note the order
    >>> point_to_polygon_dist(p, poly)
    0.5

    Notes
    -----
    This function calculates the distance of the point to each line segment
    of the polygon, and then returns the shortest distance.
    """

    # Calculate the distance to the first line segment of the polygon.
    seg_p1 = polygon[0]
    seg_p2 = polygon[1]

    dist = point_to_seg_dist(point, seg_p1, seg_p2)

    length = len(polygon)

    # Iterate over the rest of the polygon and calculate the distances to the
    # rest of the line segments.
    for i in range(1, length):
        seg_p1 = polygon[i]
        seg_p2 = polygon[(i + 1) % length]  # To wrap around once we get to the end

        current_dist = point_to_seg_dist(point, seg_p1, seg_p2)
        if current_dist < dist:
            dist = current_dist

    return dist


def point_in_polygon(point, polygon):
    """
    Calculate if a point is inside a polygon.

    This works for convex and concave simple polygons (none of the polygon edges
    intersect).

    Parameters
    ----------
    point: tuple
        The (x, y) coordinates of the point.

    polygon: list of tuples
        The (x, y) coordinates of the vertices of the polygon. These vertices
        must be "in order", meaning there is a line connecting polygon[0] to
        polygon[1], and then polygon[1] to polygon[2], etc.

        Note: Do not add the first point of the list to the end (to reflect
        the cyclic nature of the polygon); it is taken care of in the
        algorithm.

    Returns
    -------
    bool
        Indicates if the point is inside the polygon.

    References
    ----------
    This is a Python implementation of the horizontal ray casting algorithm on
    http://paulbourke.net/geometry/polygonmesh/
    (look for the point in polygon section).

    Examples
    --------
    >>> p = (0.5, 0.5)
    >>> poly = [(0, 0), (0, 1), (1, 1), (1, 0)]  # Note the order
    >>> point_in_polygon(p, poly)
    True
    """

    x, y = point
    length = len(polygon)
    inside = False

    for i in range(length):
        p1x, p1y = polygon[i]
        p2x, p2y = polygon[(i + 1) % length]  # To wrap back to first point once we reach the end
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside

    return inside
