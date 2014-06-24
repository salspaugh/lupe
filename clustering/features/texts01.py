from scipy.stats import describe

"""
This module featurizes only texts of queries i.e., the unique or distinct
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
        self.versions = ["texts01"]


class NumberOfDistinctUsersFeature(Feature):
    
    def __init__(self):
        super(NumberOfDistinctUsersFeature, self).__init__()

    def check(self, text):
        return text.distinct_users()


class NumberOfSelectedOccurrencesFeature(Feature):
    
    def __init__(self):
        super(NumberOfSelectedOccurrencesFeature, self).__init__()

    def check(self, text):
        return text.number_of_selected_occurrences()


class EntropyOfInterarrivalIntervalsFeature(Feature):
    
    def __init__(self):
        super(EntropyOfInterarrivalIntervalsFeature, self).__init__()

    def check(self, text):
        return text.interarrival_entropy()


class DescribeInterarrivalIntervalsFeature(Feature):
    
    def __init__(self):
        super(DescribeInterarrivalIntervalsFeature, self).__init__()

    def check(self, text):
        if len(text.interarrivals) == 0:
            return [0., 0., 0., 0., 0., 0., 0.] # TODO: Figure out if this is okay.
        if len(text.interarrivals) == 1:
            interarrival = text.interarrivals[0]
            return [1., interarrival, interarrival, interarrival, 0., 0., 0.] # TODO: Figure out if this is okay.
        size, (min, max), mean, var, skew, kurt = describe(text.interarrivals)
        return [size, min, max, mean, var, skew, kurt]


class RangeOfInterarrivalIntervalsFeature(Feature):
    
    def __init__(self):
        super(RangeOfInterarrivalIntervalsFeature, self).__init__()

    def check(self, text):
        if len(text.interarrivals) > 0:
            return max(text.interarrivals) - min(text.interarrivals)
        return -1.0


class NumberOfStagesFeature(Feature):
    
    def __init__(self):
        super(NumberOfStagesFeature, self).__init__()

    def check(self, text):
        return len(text.text.split("|"))


class PeriodicityFeature(Feature):
    
    def __init__(self):
        super(PeriodicityFeature, self).__init__()

    def check(self, text):
        return text.periodicity()


class ClocknessFeature(Feature):
    
    def __init__(self):
        super(ClocknessFeature, self).__init__()

    def check(self, text):
        return text.clockness()


class NumberOfNonSearchCommandsFeature(Feature):
    
    def __init__(self):
        super(NumberOfNonSearchCommandsFeature, self).__init__()

    def check(self, text):
        stages = text.text.split("|")
        commands = [s.split()[0] for s in stages if len(s) > 0]
        return len([c for c in commands if c.strip().lower() != "search"])


FEATURES = [
    NumberOfDistinctUsersFeature(),
    NumberOfSelectedOccurrencesFeature(),
    EntropyOfInterarrivalIntervalsFeature(),
    DescribeInterarrivalIntervalsFeature(),
    RangeOfInterarrivalIntervalsFeature(),
    NumberOfStagesFeature(),
    PeriodicityFeature(),
    ClocknessFeature(),
    #NumberOfNonSearchCommandsFeature()
]
