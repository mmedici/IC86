#!/usr/bin/env python

"""
Functions for plotting the charge distributions.
"""

from __future__ import print_function, unicode_literals, division  # 2to3

import argparse
import numpy as np

import matplotlib
matplotlib.use('PDF')  # Need this to stop X from launching a viewer.
import matplotlib.pyplot as plt

from calculate import process, calc_charge_info, calc_ratio_error

plot_kwargs = {}
plot_kwargs['total_charge_IC_unsplit'] = {'bins': 100, 'range': (0, 4)}
plot_kwargs['energy'] = {'bins': 24, 'range': (0, 300)}
plot_kwargs['azimuth'] = {'bins': 36, 'range': (0, 360)}
plot_kwargs['zenith'] = {'bins': 18, 'range': (0, 90)}
plot_kwargs['reco_x'] = {'bins': 24, 'range': (-600, 600)}
plot_kwargs['reco_y'] = {'bins': 24, 'range': (-600, 600)}
plot_kwargs['reco_z'] = {'bins': 20, 'range': (-400, 100)}

plot_info = {}
plot_info['total_charge_IC_unsplit'] = {'title': 'Total Charge for IC DOMs', 'xlabel': 'Charge', 'ylabel': 'Normalized Number of DOMs', 'ofile': 'total_charge_IC.pdf'}
plot_info['energy'] = {'title': 'Energy', 'xlabel': 'Energy (GeV)', 'ylabel': 'Normalized Number of Events', 'ofile': 'energy.pdf'}
plot_info['azimuth'] = {'title': 'Azimuth', 'xlabel': 'Angle', 'ylabel': 'Normalized Number of Events', 'ofile': 'azimuth.pdf',
                        'xticks': np.linspace(0, 360, 9)}
plot_info['zenith'] = {'title': 'Zenith', 'xlabel': 'Angle', 'ylabel': 'Normalized Number of Events', 'ofile': 'zenith.pdf',
                       'xticks': np.linspace(0, 90, 10)}
plot_info['reco_x'] = {'title': 'Reconstructed Endpoint (X)', 'xlabel': 'X (m)', 'ylabel': 'Normalized Number of Events', 'ofile': 'reco_x.pdf'}
plot_info['reco_y'] = {'title': 'Reconstructed Endpoint (Y)', 'xlabel': 'Y (m)', 'ylabel': 'Normalized Number of Events', 'ofile': 'reco_y.pdf'}
plot_info['reco_z'] = {'title': 'Reconstructed Endpoint (Z)', 'xlabel': 'Z (m)', 'ylabel': 'Normalized Number of Events', 'ofile': 'reco_z.pdf'}


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


def plot_distributions(data1, data2, kwargs, info, args):

    # To add the statistics boxes outside the main plotting area, the figure
    # needs to be wider than the default.
    plt.figure(figsize=(10, 6))

    # However, the dimensions of the plot remain the same (8x6).
    plt.subplot2grid((1, 9), (0, 0), colspan=8)

    # Plot the first histogram.
    plt.hist(data1, histtype='step', normed=True, label=args.label1, color='blue', **kwargs)

    # Add the first stats box.
    data1_stats = args.label1.center(17) + '\n' + stats(data1)
    plt.figtext(0.83, 0.6, data1_stats, va='center',
                bbox={'facecolor': 'w', 'pad': 10}, size=10, family='monospace')

    # Plot the second histogram.
    plt.hist(data2, histtype='step', normed=True, label=args.label2, color='red', **kwargs)

    # Add the second stats box.
    data2_stats = args.label2.center(17) + '\n' + stats(data2)
    plt.figtext(0.83, 0.4, data2_stats, va='center',
                bbox={'facecolor': 'w', 'pad': 10}, size=10, family='monospace')

    plt.title(info['title'])
    plt.xlabel(info['xlabel'])
    plt.ylabel(info['ylabel'])
    if 'xticks' in info:
        plt.xticks(info['xticks'])
    plt.legend()

    plt.savefig(args.outdir + info['ofile'])
    plt.close()


def plot_avg_charge_ratio(dataset1, dataset2, args):
    """
    Plot the ratio of dataset2 average charge / dataset1 average charge.

    Parameters
    ----------
    dataset1: dict
        Contains the data for the first dataset

    dataset2: dict
        Contains the data for the second dataset

    ratio_error: dict
        Various ratio errors.

    sys_args: dict
        System arguments.
    """

    charge_info = {}
    charge_info['1_IC'] = calc_charge_info(dataset1['total_charge_IC'])
    charge_info['1_DC'] = calc_charge_info(dataset1['total_charge_DC'])

    charge_info['2_IC'] = calc_charge_info(dataset2['total_charge_IC'])
    charge_info['2_DC'] = calc_charge_info(dataset2['total_charge_DC'])

    ratio_error_IC = calc_ratio_error(charge_info['1_IC'], charge_info['2_IC'])
    ratio_error_DC = calc_ratio_error(charge_info['1_DC'], charge_info['2_DC'])

    plt.errorbar(charge_info['1_IC']['mean_dist'], charge_info['2_IC']['charge'] / charge_info['1_IC']['charge'], ratio_error_IC, fmt='bo', label='IC DOMs')
    plt.errorbar(charge_info['1_DC']['mean_dist'], charge_info['2_DC']['charge'] / charge_info['1_DC']['charge'], ratio_error_DC, fmt='ro', label='DC DOMs')

    plt.title('Average Charge Ratio vs. Track Distance')
    plt.xlabel('Track to DOM Distance (m)')
    plt.ylabel('{}/{}'.format(args.label2, args.label1))
    plt.legend()

    plt.savefig(args.outdir + 'avg_charge_ratio.pdf')
    plt.close()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('data1', help='Dataset with lower efficiency')
    parser.add_argument('label1', help='Label for first dataset')
    parser.add_argument('data2', help='Dataset with higher efficiency')
    parser.add_argument('label2', help='Label for second dataset')
    parser.add_argument('outdir', help='Directory where plots are saved')
    args = parser.parse_args()

    if not args.outdir.endswith('/'):
        args.outdir += '/'

    dataset1 = process(args.data1)
    dataset2 = process(args.data2)

    for plot_name in plot_kwargs:
        plot_distributions(dataset1[plot_name], dataset2[plot_name], plot_kwargs[plot_name], plot_info[plot_name], args)

    plot_avg_charge_ratio(dataset1, dataset2, args)

if __name__ == '__main__':
    main()
