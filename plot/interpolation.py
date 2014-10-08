"""
Create the plot used to derive the experimental DOM efficiency.
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
from scipy import optimize
import tables


def dist_bin_split(total_charges, reco_distances):
    """
    Split apart 'total_charges' based on the corresponding reconstructed
    distances.

    Parameters
    ----------
    total_charges : 1D Numpy array
        The total charge recorded by each DOM

    reco_distance : 1D Numpy array
        The corresponding ___ for the charges.

    Returns
    -------
    split_charges : list of 1D Numpy arrays
        The charges for each bin. The charges for the first bin are in
        split_charges[0], the charges for the second in split_charges[1], etc.
    """

    # Both these numbers are in metres
    bin_width = 20
    max_dist = 140

    split_charges = []
    for dist in range(0, max_dist, bin_width):

        dist_cut = (dist <= reco_distances) & (reco_distances < dist + bin_width)

        split_charges.append(total_charges[dist_cut])

    return split_charges


def calc_charge_info(split_charges):
    """
    Calculate the average charge and error for each distance bin.

    Parameters
    ----------
    split_charges: list of 1D numpy arrays
        The charges split apart into bins. Each array has the charges for a
        particular bin.

    Returns
    -------
    mean_charges: 1D numpy array
        The average charge of each distance bin.

    errors: 1D numpy array
        The error for each average charge.
    """

    mean_charges = []
    errors = []

    for bin_charges in split_charges:

        mean_charges.append(bin_charges.mean())

        num_hits = np.count_nonzero(bin_charges)
        num_no_hits = len(bin_charges) - num_hits  # 0 in the array means no hit

        non_zero = bin_charges != 0
        non_zero_charges = bin_charges[non_zero]

        mu = non_zero_charges.mean()
        std_mu = np.std(non_zero_charges, ddof=1) / np.sqrt(num_hits)

        error = num_hits * (mu * num_no_hits) ** 2 / len(bin_charges) ** 4
        error += num_no_hits * (mu * num_hits) ** 2 / len(bin_charges) ** 4
        error += (std_mu * num_hits / len(bin_charges)) ** 2
        error **= 1 / 2

        errors.append(error)

    mean_charges = np.array(mean_charges)
    errors = np.array(errors)

    return mean_charges, errors


def process(dataset_path):
    """
    Calculate the mean_charges and errors for the dataset at the specified path.

    Parameters
    ----------
    dataset_path : str
        Path to the dataset

    Returns
    -------
    mean_charges: 1D numpy array
        The average charge of each distance bin.

    errors: 1D numpy array
        The error for each average charge.
    """

    infile = tables.open_file(dataset_path)

    reco_distance_IC = infile.root.RecoDistanceIC.cols.item[:]
    total_charge_IC = infile.root.TotalChargeIC.cols.item[:]

    infile.close()

    total_charge_IC_split = dist_bin_split(total_charge_IC, reco_distance_IC)

    mean_charges, errors = calc_charge_info(total_charge_IC_split)

    return mean_charges, errors


def main():

    ###############
    # Get Arguments
    ###############

    parser = argparse.ArgumentParser(description='script for deriving the DOM efficiency')
    parser.add_argument('-s', '--sim', help='simulated datafiles',
                        nargs='+', required=True)
    parser.add_argument('-e', '--effs', help='efficiences of the simulated datafiles',
                        nargs='+', required=True, type=float)
    parser.add_argument('-x', '--exp', help='experimental datafile',
                        required=True)
    parser.add_argument('-o', '--outdir', help='output directory',
                        required=True)

    args = parser.parse_args()

    if not args.outdir.endswith('/'):
        args.outdir += '/'

    ########
    # Errors
    ########

    # Bundle error contribution
    # (sigma_cb/cb)^2 = (sigma_cr_b/cr_b)^2 + (sigma_n_b/n_b)^2 + (sigma_n_t/n_t)^2
    # cb is contribution due to bundle
    # cr_b is charge ratio for bundles/singles
    # n_b is # of bundle DOMs
    # n_t is # of total DOMs
    # the reasoning is, the bundle contribution is cr_b*n_b/n_t
    # so, the uncertainty in the bundle contribution is the statement above
    # note that sigma_N_b should include systematic contributions due to
    # hadronic interaction model...

    n_b = 776
    n_t = n_b + 31545
    him = 0.0002 * n_t  # uncertainty on bundle percentage from had. int. model is 0.02%
    sigma_n_b = np.sqrt(n_b + him ** 2)
    sigma_n_t = np.sqrt(n_t)
    cr_b = 1.69
    sigma_cr_b = 0.11
    cb = cr_b * n_b / n_t

    bundle_error = np.sqrt((sigma_cr_b / cr_b) ** 2 + (sigma_n_b / n_b) ** 2 + (sigma_n_t / n_t) ** 2) * cb

    # SPE peak error, from fits
    # spe_correction_factor = 1.022
    # spe_charge_error = 0.0065

    # for not including SPE correction, use these:
    spe_correction_factor = 1
    spe_charge_error = 0

    # Noise error
    # NoiseCharge per event = (avg noise rate) x (1 us time window) x (2 DOMs/event) x (1 PE/hit)
    # uncertainty on noise rate is ~25%, so multiply by .25
    noise_error = 500 * 10 ** -6 / 0.7 * 1 * 0.25

    # Afterpulse error
    # http://icecube.wisc.edu/~chwendt/pmt-saturation-2005/ claims 0.0023 PE from afterpulses for every 1 primary PE, for "early" afterpulses (less than 1 us).  a 15% scatter is mentioned, so:
    # error is 0.0023 afterPE/primaryPE * 15% / 0.7 (avg. charge for relevant region)
    # http://wiki.icecube.wisc.edu/index.php/Afterpulse_Data is also relevant
    afterpulse_error = 0.0023 * 0.15 / 0.7

    ##############
    # Experimental
    ##############

    exp_charges, exp_errors = process(args.exp)

    scaled_exp_charges = exp_charges / (exp_charges * spe_correction_factor)
    scaled_exp_errors = exp_errors / exp_charges

    # Get the charges of the 20-80 m distance bins.
    exp_charges_we_want = scaled_exp_charges[1:4]
    exp_errors_we_want = scaled_exp_errors[1:4]

    avg_scaled_exp_charge = exp_charges_we_want.mean()
    avg_scaled_exp_error = np.sqrt(sum(exp_errors_we_want ** 2)) / 3  # Check this

    ############
    # Simulation
    ############

    effs = np.array(args.effs)

    sim_charges = []
    sim_errors = []
    for path in args.sim:
        charges, errors = process(path)
        sim_charges.append(charges)
        sim_errors.append(errors)

    sim_charges = np.array(sim_charges)  # 2D
    sim_errors = np.array(sim_errors)

    # Scale the simulated charges and down by the experimental charges
    scaled_sim_charges = sim_charges / exp_charges  # Scale the charges down
    scaled_sim_errors = scaled_sim_charges * np.sqrt((sim_errors / sim_charges) ** 2 + (exp_errors / exp_charges) ** 2)

    # Get the ones in 20-80 bins
    scaled_sim_charges_we_want = scaled_sim_charges[:, 1:4]
    scaled_sim_errors_we_want = scaled_sim_errors[:, 1:4]

    avg_scaled_sim_charges = scaled_sim_charges_we_want.mean(axis=1)  # Take the mean along the rows
    avg_scaled_sim_errors = np.sqrt(np.sum(scaled_sim_errors_we_want ** 2, axis=1)) / 3

    #########
    # Fitting
    #########

    # Do a linear interpolation
    (m, b), cov = optimize.curve_fit(lambda x, m, b: m * x + b, effs, avg_scaled_sim_charges, sigma=avg_scaled_sim_errors)
    fit = m * effs + b

    derived_exp_eff = (avg_scaled_exp_charge - b) / m

    # Since data statistical error is propagated through, and the ratio is defined as 1,
    # Don't include exp error here
    # TODO include hole_ice_error
    exp_yerror = (spe_charge_error ** 2 + bundle_error ** 2 + noise_error ** 2 + afterpulse_error ** 2) ** (1 / 2)

    # x = (y-b)/m, so:
    # sx^2 = 1/m^2 * [sy^2 + sb^2 + ((y-b)/m)^2*sm^2 + 2smb*(y-b)/m]

    exp_xerror = exp_yerror ** 2
    exp_xerror += cov[1, 1]
    exp_xerror += cov[0, 0] * ((avg_scaled_exp_charge - b) / m) ** 2
    exp_xerror += 2 * cov[0, 1] * (avg_scaled_exp_charge - b) / m
    exp_xerror /= m ** 2
    exp_xerror **= 1 / 2

    ##########
    # Plotting
    ##########

    # Plot the simulation points and the fit
    plt.errorbar(effs, avg_scaled_sim_charges, avg_scaled_sim_errors, linestyle='None', color='r', marker='o', label='Simulation')
    plt.plot(effs, fit, color='r')

    # Plot the experimental datapoint
    plt.errorbar(derived_exp_eff, avg_scaled_exp_charge, xerr=exp_xerror, yerr=exp_yerror, color='b', marker='o', label='Experiment')

    plt.title('Scaled Average Charge vs. Simulated DOM Efficiency')
    plt.xlabel('Simulated DOM Efficiency')
    plt.ylabel('Scaled Average Charge')
    plt.legend(loc='upper left')

    plt.xlim(effs.min() - 0.1, effs.max() + 0.1)
    plt.ylim(effs.min() - 0.1, effs.max() + 0.1)
    plt.figtext(0.8, 0.8, r'$ m = {:.3f}$'.format(m))

    plt.savefig(args.outdir + 'scaled_average_charge.pdf')

if __name__ == '__main__':
    main()
