#!/usr/bin/env python

"""
Compare the zenith, azimuth, energy, and other such things of the provided
data files.
"""

from __future__ import print_function, unicode_literals, division  # 2to3

import argparse
import numpy as np
import tables

import matplotlib
matplotlib.use('PDF')  # Need this to stop X from launching a viewer.
import matplotlib.pyplot as plt

plot_kwargs = {}

plot_kwargs['reco_endpoint_x'] = {'bins': 24, 'range': (-600, 600)}
plot_kwargs['reco_endpoint_y'] = {'bins': 24, 'range': (-600, 600)}
plot_kwargs['reco_endpoint_z'] = {'bins': 20, 'range': (-400, 100)}

plot_kwargs['energy'] = {'bins': 24, 'range': (0, 300)}
plot_kwargs['azimuth'] = {'bins': 36, 'range': (0, 360)}
plot_kwargs['zenith'] = {'bins': 36, 'range': (0, 90)}

plot_kwargs['total_charge_IC'] = {'bins': 100, 'range': (0, 4)}
plot_kwargs['total_charge_DC'] = {'bins': 100, 'range': (0, 4)}


plot_info = {}

plot_info['reco_endpoint_x'] = {'title': 'Reconstructed Endpoint X', 'xlabel': 'X (m)', 'ylabel': 'Normalized Number of Events', 'ofile': 'reco_x.pdf'}
plot_info['reco_endpoint_y'] = {'title': 'Reconstructed Endpoint Y', 'xlabel': 'Y (m)', 'ylabel': 'Normalized Number of Events', 'ofile': 'reco_y.pdf'}
plot_info['reco_endpoint_z'] = {'title': 'Reconstructed Endpoint Z', 'xlabel': 'Z (m)', 'ylabel': 'Normalized Number of Events', 'ofile': 'reco_z.pdf'}

plot_info['energy'] = {'title': 'Energy', 'xlabel': 'Energy (GeV)', 'ylabel': 'Normalized Number of Events', 'ofile': 'energy.pdf'}
plot_info['azimuth'] = {'title': 'Azimuth', 'xlabel': 'Angle', 'ylabel': 'Normalized Number of Events', 'ofile': 'azimuth.pdf', 'xticks': np.linspace(0, 360, 9)}
plot_info['zenith'] = {'title': 'Zenith', 'xlabel': 'Angle', 'ylabel': 'Normalized Number of Events', 'ofile': 'zenith.pdf', 'xticks': np.linspace(0, 90, 10)}

plot_info['total_charge_IC'] = {'title': 'Total Charge for IC DOMs (Reco Singles + Bundles)', 'xlabel': 'Charge', 'ylabel': 'Normalized Number of DOMs', 'ofile': 'total_charge_IC.pdf'}
plot_info['total_charge_DC'] = {'title': 'Total Charge for DC DOMs (Reco Singles + Bundles)', 'xlabel': 'Charge', 'ylabel': 'Normalized Number of DOMs', 'ofile': 'total_charge_DC.pdf'}


def process(dataset_path):

    dataset = {}

    infile = tables.open_file(dataset_path)

    dataset['reco_endpoint_x'] = infile.root.RecoEndpoint.cols.x[:]
    dataset['reco_endpoint_y'] = infile.root.RecoEndpoint.cols.y[:]
    dataset['reco_endpoint_z'] = infile.root.RecoEndpoint.cols.z[:]

    dataset['azimuth'] = np.degrees(infile.root.MPEFit.cols.azimuth[:])
    dataset['zenith'] = np.degrees(infile.root.MPEFit.cols.zenith[:])
    dataset['energy'] = infile.root.FiniteRecoFit.cols.length[:] / 4.5

    total_charge_IC = infile.root.TotalChargeIC.cols.item[:]
    total_charge_DC = infile.root.TotalChargeDC.cols.item[:]

    dataset['total_charge_IC'] = total_charge_IC[total_charge_IC != 0]
    dataset['total_charge_DC'] = total_charge_DC[total_charge_DC != 0]

    infile.close()

    return dataset


def stats(array):
    """
    Make a string containing statistics.

    The length, median, mean, and standard deviation of the array are
    calculated.

    Parameters
    ----------
    array: np.ndarray
        Data to make stats on.

    Returns
    -------
    str
        The stats on the input array.
    """

    num = len(array)
    median = np.median(array)
    mean = np.mean(array)
    std = np.std(array)

    string = 'Entries{:10}\nMedian{:11.4f}\nMean{:13.4f}\nSt Dev{:11.4f}'.format(num, median, mean, std)

    return string


def plot_distributions(data, kwargs, info, args):

    # The y coordinates of the stats boxes for the various numbers of datasets.
    y_coords = {}
    y_coords[1] = [0.5]
    y_coords[2] = [0.6, 0.4]
    y_coords[3] = [0.7, 0.5, 0.3]
    y_coords[4] = [0.8, 0.6, 0.4, 0.2]

    # To add the statistics boxes outside the main plotting area, the figure
    # needs to be wider than the default.
    plt.figure(figsize=(10, 6))

    # However, the dimensions of the plot remain the same (8x6).
    plt.subplot2grid((1, 9), (0, 0), colspan=8)

    for i in range(len(data)):
        plt.hist(data[i], histtype='step', weights=np.ones(len(data[i])) / len(data[i]), label=args.labels[i], **kwargs)
        data_stats = args.labels[i].center(17) + '\n' + stats(data[i])
        plt.figtext(0.83, y_coords[len(data)][i], data_stats, va='center',
                    bbox={'facecolor': 'w', 'pad': 10}, size=10, family='monospace')

    plt.title(info['title'])
    plt.xlabel(info['xlabel'])
    plt.ylabel(info['ylabel'])
    if 'xticks' in info:
        plt.xticks(info['xticks'])
    plt.legend()

    plt.savefig(args.outdir + info['ofile'])
    plt.close()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--datasets', help='paths to the datasets',
                        nargs='+', required=True)
    parser.add_argument('-l', '--labels', help='labels for the datasets',
                        nargs='+', required=True)
    parser.add_argument('-o', '--outdir', help='output directory to save plots',
                        required=True)
    args = parser.parse_args()

    if not args.outdir.endswith('/'):
        args.outdir += '/'

    datasets = []
    for path in args.datasets:
        dataset = process(path)
        datasets.append(dataset)

    for plot_name in plot_kwargs:
        data = [dataset[plot_name] for dataset in datasets]
        plot_distributions(data, plot_kwargs[plot_name], plot_info[plot_name], args)

if __name__ == '__main__':
    main()
