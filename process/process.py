#!/usr/bin/env python

"""
Process the I3 files.
"""

from __future__ import print_function, division  # 2to3

import argparse

from icecube import dataio, icetray, gulliver, simclasses, dataclasses, photonics_service, phys_services
from icecube.common_variables import direct_hits, hit_multiplicity, hit_statistics
from I3Tray import I3Tray, I3Units, load

from filters import in_ice, min_bias, SMT8, MPEFit, InIceSMTTriggered
from general import get_truth_muon, get_truth_endpoint, count_hits, reco_endpoint, move_cut_variables
from geoanalysis import calc_dist_to_border
from domanalysis import om_partition, dom_data

load('libipdf')
load('libgulliver')
load('libgulliver-modules')
load('liblilliput')
load('libstatic-twc')
load('libjeb-filter-2012')


def main():

    parser = argparse.ArgumentParser(description='script for proccessing I3 files')
    parser.add_argument('gcd', help='GCD file for the data')
    parser.add_argument('data', help='data file for processing')
    parser.add_argument('ofile', help='name of output file')
    parser.add_argument('-s', '--sim', help='turn on extra processing for sim files',
                        action='store_true')
    args = parser.parse_args()

    # Don't touch, unless you know what you're doing
    options = {}
    options['pulses_name'] = 'TWSRTOfflinePulses'
    options['max_dist'] = 140
    options['partitions'] = 5

    tray = I3Tray()

    # Read the files.
    tray.AddModule('I3Reader', 'I3Reader',
                   Filenamelist=[args.gcd, args.data])

    # Filters

    # Filter the ones with sub_event_stream == in_ice
    tray.AddModule(in_ice, 'in_ice')

    # Check in FilterMinBias_11 that condition_passed and prescale_passed are both true
    tray.AddModule(min_bias, 'min_bias')

    # Make sure that the length of TWOfflinePulsesHLC is >= 8
    tray.AddModule(SMT8, 'SMT8')

    # Check that the fit_status of MPEFit is OK, and that 40 < zenith < 70
    tray.AddModule(MPEFit, 'MPEFit')

    # Trigger check
    # jeb-filter-2012
    tray.AddModule('TriggerCheck_12', 'TriggerCheck_12',
                   I3TriggerHierarchy='I3TriggerHierarchy',
                   InIceSMTFlag='InIceSMTTriggered',
                   IceTopSMTFlag='IceTopSMTTriggered',
                   InIceStringFlag='InIceStringTriggered',
                   PhysMinBiasFlag='PhysMinBiasTriggered',
                   PhysMinBiasConfigID=106,
                   DeepCoreSMTFlag='DeepCoreSMTTriggered',
                   DeepCoreSMTConfigID=1010)

    # Check that InIceSMTTriggered is true.
    tray.AddModule(InIceSMTTriggered, 'InIceSMTTriggered')

    # Endpoint

    # Add the reconstructed event endpoint to the frame.
    tray.AddModule(reco_endpoint, 'reco_endpoint',
                   endpoint_fit='FiniteRecoFit')

    # Domanalysis

    # Recalculate recos on subset of Doms (above dust layer)
    # lilliput
    tray.AddService('I3SimpleParametrizationFactory', 'SimpleTrack',
                    StepX=20 * I3Units.m,                              # Set to 1/50 the size of the detector
                    StepY=20 * I3Units.m,                              # Set to 1/50 the size of the detector
                    StepZ=20 * I3Units.m,                              # Set to 1/50 the size of the detector
                    StepZenith=0.1 * I3Units.radian,                   # Set to 1/30 the size of the detector
                    StepAzimuth=0.2 * I3Units.radian,                  # Set to 1/30 the size of the detector
                    StepLinE=0,                                        # Default
                    StepLogE=0,                                        # Default
                    StepT=0,                                           # Default
                    BoundsAzimuth=[0, 0],                              # Default
                    BoundsZenith=[0, 0],                               # Default
                    BoundsT=[0, 0],                                    # Default
                    BoundsX=[-2000 * I3Units.m, +2000 * I3Units.m],    # Set bounds to twice the size of the detector
                    BoundsY=[-2000 * I3Units.m, +2000 * I3Units.m],    # Set bounds to twice the size of the detector
                    BoundsZ=[-2000 * I3Units.m, +2000 * I3Units.m])    # Set bounds to twice the size of the detector

    # lilliput
    tray.AddService('I3GulliverMinuitFactory', 'Minuit',
                    Algorithm='SIMPLEX',    # Default
                    FlatnessCheck=True,     # Default
                    MaxIterations=1000,     # Only need 1000 iterations
                    MinuitPrintLevel=-2,    # Default
                    MinuitStrategy=2,       # Default
                    Tolerance=0.01)         # Set tolerance to 0.01

    # Seed the reduced SPESingle with the full SPESingle
    # lilliput
    tray.AddService('I3BasicSeedServiceFactory', 'MPESeed',
                    InputReadout=options['pulses_name'],
                    TimeShiftType='TFirst',
                    FirstGuesses=['MPEFit'])

    # Subset reconstruction time. This is slightly complicated. Each DOM is
    # placed into a partition based on (dom.string + dom.om) %
    # options['partitions']. So if a certain dom has (dom.string + dom.om) % 5
    # = 1 (right now options['partitions'] is 5), then that DOM is in the 1
    # partition. Now, when we do the fitter/pandel/reconstruction thing for
    # a particular partition, we want to do it on all the doms EXCEPT the ones
    # in that partition (this is that cross-validation). This is what
    # om_selection does. It lumps together all the TWSRTOfflinePulses for the
    # doms not in a particular partition into InIceRecoPulseSeriesPattern0...4. For
    # example, InIceRecoPulseSeriesPattern1 contains all the pulses except the
    # ones for the doms in the 1 partition. This is then fed into the
    # PandelFactory and the SimpleFitter.
    output_name = 'InIceRecoPulseSeriesPattern{}'

    tray.AddModule(om_partition, 'om_partition',
                   output_name=output_name,
                   options=options)

    for partition in range(options['partitions']):
        # lilliput
        tray.AddService('I3GulliverIPDFPandelFactory', 'MPEPandel{}'.format(partition),
                        InputReadout=output_name.format(partition),    # Use pulses given to thes function as arg
                        EventType='InfiniteMuon',                      # Default
                        Likelihood='MPE',                              # MPE
                        PEProb='GaussConvolutedFastApproximation',     # New approximation for convaluted
                        IceModel=2,                                    # Default
                        IceFile='',                                    # Default
                        AbsorptionLength=98.0 * I3Units.m,             # Default
                        JitterTime=4.0 * I3Units.ns,                   # Use small jitter time
                        NoiseProbability=10 * I3Units.hertz)           # Added a little noise term

        # gulliver-modules
        tray.AddModule('I3SimpleFitter', 'MPEFit{}'.format(partition),
                       # RandomService=SOBOL,                          # Name of randomizer service
                       SeedService='MPESeed',                          # Name of seed service
                       Parametrization='SimpleTrack',                  # Name of track parametrization service
                       LogLikelihood='MPEPandel{}'.format(partition),  # Name of likelihood service
                       Minimizer='Minuit')                             # Name of minimizer service

    # This uses the MPEFit's to calculate TotalCharge, RecoDistance, etc.
    tray.AddModule(dom_data, 'dom_data',
                   reco_fit='MPEFit{}',
                   options=options)

    # General

    # Calculate cut variables
    tray.AddSegment(direct_hits.I3DirectHitsCalculatorSegment, 'I3DirectHits',
                    PulseSeriesMapName=options['pulses_name'],
                    ParticleName='MPEFit',
                    OutputI3DirectHitsValuesBaseName='MPEFitDirectHits')

    tray.AddSegment(hit_multiplicity.I3HitMultiplicityCalculatorSegment, 'I3HitMultiplicity',
                    PulseSeriesMapName=options['pulses_name'],
                    OutputI3HitMultiplicityValuesName='HitMultiplicityValues')

    tray.AddSegment(hit_statistics.I3HitStatisticsCalculatorSegment, 'I3HitStatistics',
                    PulseSeriesMapName=options['pulses_name'],
                    OutputI3HitStatisticsValuesName='HitStatisticsValues')

    # Move the cut variables into the top level of the frame.
    tray.AddModule(move_cut_variables, 'move_cut_variables',
                   direct_hits_name='MPEFitDirectHits',
                   hit_multiplicity_name='HitMultiplicityValues'
                   fit_params_name='MPEFitFitParams')

    # Calculate ICAnalysisHits, DCAnalysisHits, ICNHits, and DCNHits
    tray.AddModule(count_hits, 'count_hits',
                   pulses_name=options['pulses_name'])

    if args.sim:
        # Count the number of in ice muons and get the truth muon
        tray.AddModule(get_truth_muon, 'get_truth_muon')
        tray.AddModule(get_truth_endpoint, 'get_truth_endpoint')

    # Geoanalysis

    # Calculate the distance of each event to the detector border.
    tray.AddModule(calc_dist_to_border, 'calc_dist_to_border')

    # Write out the data to an I3 file
    tray.AddModule('I3Writer', 'I3Writer',
                   FileName=args.ofile,
                   SkipKeys=['InIceRecoPulseSeriesPattern.*'],
                   DropOrphanStreams=[icetray.I3Frame.DAQ],
                   Streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics])

    tray.Execute()
    tray.Finish()

if __name__ == '__main__':
    main()
