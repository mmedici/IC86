"""
This module contains functions for calculating the average charge for each bin from the total_charge_dict.
"""

from __future__ import print_function, unicode_literals, division  # 2to3

from collections import OrderedDict

import numpy as np
import tables


def dist_bin_split(data, reco_distance):
    bin_width = 20  # Hard coded in here for now
    max_dist = 140

    data_dict = OrderedDict()

    for dist in range(0, max_dist, bin_width):

        dist_cut = (dist <= reco_distance) & (reco_distance < dist + bin_width)

        key = (dist, dist + bin_width)
        data_dict[key] = data[dist_cut]

    return data_dict


def process(dataset_path):

    infile = tables.open_file(dataset_path)

    dataset = {}

    dataset['reco_x'] = infile.root.RecoEndpoint.cols.x[:]
    dataset['reco_y'] = infile.root.RecoEndpoint.cols.y[:]
    dataset['reco_z'] = infile.root.RecoEndpoint.cols.z[:]

    dataset['azimuth'] = np.degrees(infile.root.FiniteRecoFit.cols.azimuth[:])
    dataset['zenith'] = np.degrees(infile.root.FiniteRecoFit.cols.zenith[:])
    dataset['energy'] = infile.root.FiniteRecoFit.cols.length[:] / 4.5

    reco_distance_IC = infile.root.RecoDistanceIC.cols.item[:]
    reco_distance_DC = infile.root.RecoDistanceDC.cols.item[:]

    total_charge_IC = infile.root.TotalChargeIC.cols.item[:]
    total_charge_DC = infile.root.TotalChargeDC.cols.item[:]

    infile.close()

    dataset['total_charge_IC_unsplit'] = total_charge_IC

    dataset['total_charge_IC'] = dist_bin_split(total_charge_IC, reco_distance_IC)
    dataset['total_charge_DC'] = dist_bin_split(total_charge_DC, reco_distance_DC)

    return dataset


def calc_charge_info(total_charge_dict):
    """
    Calculate the mean distance of the bin, probability (of being hit?), (average) charge, and error in average charge.

    Parameters
    ----------
    total_charge_dict: dict
        Contains the total_charge_dict data.

    Returns
    -------
    charge_info: dict
        Contains the mean distance, probability, charge, and error of each thing.
    """

    mean_dist = []
    prob = []
    charge = []
    error = []

    for bounds, data in total_charge_dict.items():  # In order iteration, b/c total_charge_dict is OrderedDict
        num_hits = np.count_nonzero(data)
        num_no_hits = len(data) - num_hits  # 0 in the array means no hit

        mean_dist.append(np.mean(bounds))
        prob.append(num_hits / len(data))
        charge.append(np.mean(data))

        non_zero = data != 0
        non_zero_data = data[non_zero]

        mu = np.mean(non_zero_data)
        std_mu = np.std(non_zero_data, ddof=1) / np.sqrt(num_hits)

        error_temp = num_hits * (mu * num_no_hits) ** 2 / len(data) ** 4
        error_temp += num_no_hits * (mu * num_hits) ** 2 / len(data) ** 4
        error_temp += (std_mu * num_hits / len(data)) ** 2
        error_temp **= 1 / 2  # TODO is this the right place to take the sqrt?

        error.append(error_temp)

    charge_info = {}
    charge_info['mean_dist'] = np.array(mean_dist)
    charge_info['prob'] = np.array(prob)
    charge_info['charge'] = np.array(charge)
    charge_info['error'] = np.array(error)

    return charge_info


def calc_ratio_error(charge_info1, charge_info2):
    """
    Calculate some ratio error of charge_info2 to charge_info1. I don't know what this does exactly.

    Parameters
    ----------
    charge_info1: dict
        First information dict.

    charge_info2: dict
        Second information dict.

    Returns
    -------
    ratio_error: float
        So ratio error of the two.
    """

    ratio_error = (charge_info1['error'] / charge_info1['charge']) ** 2
    ratio_error += (charge_info2['error'] / charge_info2['charge']) ** 2
    ratio_error **= 1 / 2
    ratio_error *= charge_info2['charge'] / charge_info1['charge']

    return ratio_error
