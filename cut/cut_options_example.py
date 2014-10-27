import operator as op

import numpy as np

IC_strings = [26, 27, 37, 46, 45, 35, 17, 18, 19, 28, 38, 47, 56, 55, 54, 44, 34, 25]
DC_strings = [81, 82, 83, 84, 85, 86]

# The event cuts to make. Change these as much as you like.
event_cuts = {}
event_cuts['NDirDoms'] = (op.gt, 5)
event_cuts['rlogl'] = (op.lt, 10)
event_cuts['ICNHits'] = (op.lt, 20)
event_cuts['RecoEndpointZ'] = (op.gt, -400)
event_cuts['DistToBorder'] = (op.gt, 50)
event_cuts['ICAnalysisHits'] = (op.gt, 0)

# The dom cuts to make. Change these freely.
dom_cuts = {}
dom_cuts['String'] = (np.in1d, IC_strings)
dom_cuts['ImpactAngle'] = (op.lt, np.pi / 2)  # Must be radians
dom_cuts['DistAboveEndpoint'] = (op.gt, 100)

# The keys containing the per DOM data
dom_keys = ['TotalCharge', 'String', 'OM', 'DistAboveEndpoint', 'ImpactAngle', 'RecoDistance']
