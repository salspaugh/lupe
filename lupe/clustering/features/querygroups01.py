from scipy.stats import describe

"""
This module featurizes only querygroups of queries i.e., the unique or distinct
statement of commands that go into a query and all occurrences of it.

Features include:

    Done:
    - number of distinct users
    - number of all occurrences
    - entropy of interarrival intervals
    - describe interarrival intervals
    - range of interarrival intervals
    - number of stages
    - number of non-search commands
    - periodicity: how often queries reexecute at the same interval
    - clockness: how often queries execute at multiples of 30 seconds
    TODO:
    - number of each different command
    - length of search
"""

class Feature(object):

    def __init__(self):
        self.versions = ["querygroups01"]


class NumberOfDistinctUsersFeature(Feature):
    
    def __init__(self):
        super(NumberOfDistinctUsersFeature, self).__init__()

    def check(self, querygroup):
        return querygroup.number_of_distinct_users()


class NumberOfCopiesFeature(Feature):
    
    def __init__(self):
        super(NumberOfCopiesFeature, self).__init__()

    def check(self, querygroup):
        return querygroup.number_of_copies()


class EntropyOfInterarrivalIntervalsFeature(Feature):
    
    def __init__(self):
        super(EntropyOfInterarrivalIntervalsFeature, self).__init__()

    def check(self, querygroup):
        return querygroup.interarrival_entropy()


class DescribeInterarrivalIntervalsFeature(Feature):
    
    def __init__(self):
        super(DescribeInterarrivalIntervalsFeature, self).__init__()

    def check(self, querygroup):
        if len(querygroup.interarrivals) == 0:
            return [0., 0., 0., 0., 0., 0., 0.] # TODO: Figure out if this is okay.
        if len(querygroup.interarrivals) == 1:
            interarrival = querygroup.interarrivals[0]
            return [1., interarrival, interarrival, interarrival, 0., 0., 0.] # TODO: Figure out if this is okay.
        size, (min, max), mean, var, skew, kurt = describe(querygroup.interarrivals)
        return [size, min, max, mean, var, skew, kurt]


class RangeOfInterarrivalIntervalsFeature(Feature):
    
    def __init__(self):
        super(RangeOfInterarrivalIntervalsFeature, self).__init__()

    def check(self, querygroup):
        if len(querygroup.interarrivals) > 0:
            return max(querygroup.interarrivals) - min(querygroup.interarrivals)
        return -1.0


class NumberOfStagesFeature(Feature):
    
    def __init__(self):
        super(NumberOfStagesFeature, self).__init__()

    def check(self, querygroup):
        return len(querygroup.query.text.split("|"))


class InterarrivalConsistencyFeature(Feature):
    
    def __init__(self):
        super(InterarrivalConsistencyFeature, self).__init__()

    def check(self, querygroup):
        return querygroup.interarrival_consistency()


class InterarrivalClocknessFeature(Feature):
    
    def __init__(self):
        super(InterarrivalClocknessFeature, self).__init__()

    def check(self, querygroup):
        return querygroup.interarrival_clockness()


class NumberOfNonSearchCommandsFeature(Feature):
    
    def __init__(self):
        super(NumberOfNonSearchCommandsFeature, self).__init__()

    def check(self, querygroup):
        stages = querygroup.querygroup.split("|")
        commands = [s.split()[0] for s in stages if len(s) > 0]
        return len([c for c in commands if c.strip().lower() != "search"])


FEATURES = [
    NumberOfDistinctUsersFeature(),
    NumberOfCopiesFeature(),
    EntropyOfInterarrivalIntervalsFeature(),
    DescribeInterarrivalIntervalsFeature(),
    RangeOfInterarrivalIntervalsFeature(),
    NumberOfStagesFeature(),
    InterarrivalConsistencyFeature(),
    InterarrivalClocknessFeature(),
    #NumberOfNonSearchCommandsFeature(),
]
