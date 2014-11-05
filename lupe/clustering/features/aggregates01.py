from numpy import mean
from string import digits

"""
This module featurizes only aggregate stages.

Features include:
    - what command is used
    - what position the command is used in
    - number of distinct fields
    - aggregate function used
    - number of fields aggregated
    - number of fields grouped by
    - whether it reorders and limits
    - whether it is likely intended for a visualization 
    TODO: these can't be done if there are multiple aggregates
    - what type of data the aggregates take as input
    - what type of data the aggregates output
""" 

AGGREGATE_FUNCTIONS = []


class Feature(object):

    def __init__(self):
        self.versions = ["aggregates01"]
    
    def is_field(self, node):
        return node.role.find("FIELD") > -1
    
    def get_command(self, tree):
        for node in tree.itertree():
            if node.role == "COMMAND": return node

    def is_aggregate_function(self, node, function):
        return node.role == "FUNCTION" and node.raw == function

    def is_percentile_function(self, node):
        ptile = len(node.raw) > 1 and node.raw[0] == "p" and \
            all([True if d in digits else False for d in node.raw[1:]])
        perctile = len(node.raw) > 4 and node.raw[0:4] == "perc" and \
            all([True if d in digits else False for d in node.raw[4:]])
        percentile = ptile or perctile
        return node.role == "FUNCTION" and percentile

    def is_aggregated_field(self, node):
        return node.role == "FIELD" and \
            node.parent.role == "FUNCTION" and \
            node.parent.raw in AGGREGATE_FUNCTIONS

    def is_grouping_field(self, node):
        return node.role.find("GROUPING_FIELD") > -1


class NumberOfDistinctFieldsFeature(Feature):
    
    def __init__(self):
        super(NumberOfDistinctFieldsFeature, self).__init__()

    def check(self, aggregate):
        field_nodes = [node for node in aggregate.itertree() if self.is_field(node)]
        return len(set([node.raw for node in field_nodes]))


class SpecifiedCommandUsedFeature(Feature):

    def __init__(self, command):
        super(SpecifiedCommandUsedFeature, self).__init__()
        self.command = command

    def check(self, aggregate):
        return int(self.command == self.get_command(aggregate).raw)


class PositionInQueryFeature(Feature):
    
    def __init__(self):
        super(PositionInQueryFeature, self).__init__()

    def check(self, aggregate):
        return aggregate.position


class NumberTimesAggregateFunctionUsedFeature(Feature):
    
    def __init__(self, function):
        super(NumberTimesAggregateFunctionUsedFeature, self).__init__()
        self.function = function

    def check(self, aggregate):
        return sum([1 if self.is_aggregate_function(node, self.function) else 0 for node in aggregate.itertree()]) 


class NumberTimesPercentileFunctionUsedFeature(Feature):
    
    def __init__(self):
        super(NumberTimesPercentileFunctionUsedFeature, self).__init__()

    def check(self, aggregate):
        return sum([1 if self.is_percentile_function(node) else 0 for node in aggregate.itertree()]) 


class NumberOfFieldsAggregatedFeature(Feature):
    
    def __init__(self):
        super(NumberOfFieldsAggregatedFeature, self).__init__()

    def check(self, aggregate):
        aggregated_fields = [node.raw for node in aggregate.itertree() if self.is_aggregated_field(node)]
        return len(set(aggregated_fields))


class NumberOfFieldsGroupedByFeature(Feature):
    
    def __init__(self):
        super(NumberOfFieldsGroupedByFeature, self).__init__()

    def check(self, aggregate):
        return sum([1 if self.is_grouping_field(node) else 0 for node in aggregate.itertree()])


class ReordersAndLimitsResultsFeature(Feature):
    
    def __init__(self):
        super(ReordersAndLimitsResultsFeature, self).__init__()

    def check(self, aggregate):
        return int(self.get_command(aggregate).raw in ["rare", "top"])


class ForVisualizationFeature(Feature):
    
    def __init__(self):
        super(ForVisualizationFeature, self).__init__()

    def check(self, aggregate):
        return int(self.get_command(aggregate).raw in ["timechart", "chart"])


class InputDatatypeUsedFeature(Feature):
    
    def __init__(self):
        super(InputDatatypeUsedFeature, self).__init__()

    def check(self, aggregate):
        pass


class OutputDatatypeUsedFeature(Feature):
    
    def __init__(self):
        super(OutputDatatypeUsedFeature, self).__init__()

    def check(self, aggregate):
        pass


FEATURES = [
    NumberOfDistinctFieldsFeature(),
    SpecifiedCommandUsedFeature("addtotals"),
    SpecifiedCommandUsedFeature("addcoltotals"),
    SpecifiedCommandUsedFeature("chart"),
    SpecifiedCommandUsedFeature("eventcount"),
    SpecifiedCommandUsedFeature("geostats"),
    SpecifiedCommandUsedFeature("mvcombine"),
    SpecifiedCommandUsedFeature("rare"),
    SpecifiedCommandUsedFeature("stats"),
    SpecifiedCommandUsedFeature("timechart"),
    SpecifiedCommandUsedFeature("top"),
    SpecifiedCommandUsedFeature("transaction"),
    SpecifiedCommandUsedFeature("tstats"), 
    PositionInQueryFeature(),
    NumberTimesAggregateFunctionUsedFeature("avg"),
    NumberTimesAggregateFunctionUsedFeature("c"),
    NumberTimesAggregateFunctionUsedFeature("count"),
    NumberTimesAggregateFunctionUsedFeature("dc"),
    NumberTimesAggregateFunctionUsedFeature("distinct_count"),
    NumberTimesAggregateFunctionUsedFeature("earliest"),
    NumberTimesAggregateFunctionUsedFeature("estdc"),
    NumberTimesAggregateFunctionUsedFeature("estdc_error"),
    NumberTimesAggregateFunctionUsedFeature("first"),
    NumberTimesAggregateFunctionUsedFeature("last"),
    NumberTimesAggregateFunctionUsedFeature("latest"),
    NumberTimesAggregateFunctionUsedFeature("list"),
    NumberTimesAggregateFunctionUsedFeature("max"),
    NumberTimesAggregateFunctionUsedFeature("mean"),
    NumberTimesAggregateFunctionUsedFeature("median"),
    NumberTimesAggregateFunctionUsedFeature("min"),
    NumberTimesAggregateFunctionUsedFeature("mode"),
    NumberTimesAggregateFunctionUsedFeature("per_day"),
    NumberTimesAggregateFunctionUsedFeature("per_hour"),
    NumberTimesAggregateFunctionUsedFeature("per_minute"),
    NumberTimesAggregateFunctionUsedFeature("per_second"),
    NumberTimesAggregateFunctionUsedFeature("range"),
    NumberTimesAggregateFunctionUsedFeature("stdev"),
    NumberTimesAggregateFunctionUsedFeature("stdevp"),
    NumberTimesAggregateFunctionUsedFeature("sumsq"),
    NumberTimesAggregateFunctionUsedFeature("values"),
    NumberTimesAggregateFunctionUsedFeature("var"),
    NumberTimesAggregateFunctionUsedFeature("varp"),
    NumberTimesPercentileFunctionUsedFeature(),
    NumberOfFieldsAggregatedFeature(),
    NumberOfFieldsGroupedByFeature(),
    ReordersAndLimitsResultsFeature(),
    ForVisualizationFeature()
]

