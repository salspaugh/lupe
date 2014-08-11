from numpy import mean

"""
This module featurizes only filter stages.

Features include:
    - what command is used
    - what position the command is used in
    - does the command remove duplicates
    - does the command filter based on position
    - number of arguments
    - number of conditionals
    - number of wildcard matches (e.g., *)
    - number of ANDs
    - number of ORs
    - number of NOTs
    - number of field searches
    - number of option searches (includes search and time modifiers)
    - number of string searches
    - number of logical operators (e.g., <, >, !=, etc.)
    - number of time modifiers (e.g., earliest, latest, etc.)
    - number of subsearches (e.g., [ ... ])
    - number of searches on Splunk internal data (e.g., indexes that start with '_')?
    - number of default fields (e.g., source, sourcetype, host, etc.)
    - average length of non-field search strings
    - number of distinct fields

""" 



class Feature(object):

    def __init__(self):
        self.versions = ["filters01"]
    
    def is_wildcard_match(self, node, specific=""):
        return node.raw.find('*') > -1

    def is_conditional(self, node, specific=""):
        conditionals = ["AND", "OR", "NOT"] if not specific else [specific]
        return node.role == "FUNCTION" and node.raw in conditionals
    
    def is_field(self, node):
        return node.role.find("FIELD") > -1

    def is_field_search(self, node):
        return node.role == "FUNCTION" and \
                node.raw in ["eq", "gt", "lt", "le", "ge", "ne"] and \
                self.is_field(node.children[0]) and \
                node.children[1].role == "VALUE"
    
    def is_option_search(self, node):
        return node.role == "FUNCTION" and \
                node.raw == "eq" and \
                node.children[0].role == "OPTION" and \
                node.children[1].role == "VALUE"

    def is_string_search(self, node):
        return node.role == "FUNCTION" and node.raw == "contains"

    def is_logical_operator(self, node):
        logical_operators = ["eq", "neq", "lt", "le", "gt", "ge", "deq"]
        return node.role == "FUNCTION" and node.raw in logical_operators
    
    def is_time_modifier(self, node):
        time_modifiers = [
            "daysago", "enddaysago", "endhoursago", "endminutesago", "endmonthsago",
            "endtime", "endtimeu", "hoursago", "minutesago", "monthsago",
            "searchtimespandays", "searchtimespanhours", "searchtimespanminutes", "searchtimespanmonths",
            "startdaysago", "starthoursago", "startminutesago", "startmonthsago", "starttime", "starttimeu",
            "timeformat", "earliest", "_index_earliest", "_index_latest", "latest"
        ]
        return node.role == "FUNCTION" and node.raw == "eq" and \
                node.children[0].role == "OPTION" and \
                node.children[0].raw in time_modifiers
    
    def is_subsearch(self, node):
        return node.role == "SUBSEARCH"
    
    def is_internal_data(self, node):
        return len(node.raw) > 0 and node.raw[0] == '_'
    
    def is_default_field(self, node):
        return node.role == "DEFAULT_FIELD" and not node.raw == "timestamp"
    
    def is_default_datetime(self, node):
        return node.role == "DEFAULT_DATETIME_FIELD" or (node.role == "DEFAULT_FIELD" and node.raw == "timestamp")

    def get_command(self, tree):
        for node in tree.itertree():
            if node.role == "COMMAND": return node


class NumberOfArgumentsFeature(Feature):

    def __init__(self):
        super(NumberOfArgumentsFeature, self).__init__()

    def check(self, filter):
        return sum([1 if node.role == "FUNCTION" else 0 for node in filter.itertree()])


class NumberOfWildcardMatchesFeature(Feature):
    
    def __init__(self):
        super(NumberOfWildcardMatchesFeature, self).__init__()

    def check(self, filter):
        return sum([1 if self.is_wildcard_match(node) else 0 for node in filter.itertree()])


class NumberOfConditionalsFeature(Feature):
    
    def __init__(self):
        super(NumberOfConditionalsFeature, self).__init__()

    def check(self, filter):
        return sum([1 if self.is_conditional(node) else 0 for node in filter.itertree()])


class NumberOfSpecificConditionalsFeature(Feature):
    
    def __init__(self, conditional):
        super(NumberOfSpecificConditionalsFeature, self).__init__()
        self.conditional = conditional

    def check(self, filter):
        return sum([1 if self.is_conditional(node, specific=self.conditional) else 0 for node in filter.itertree()])


class NumberOfFieldSearchesFeature(Feature):
    
    def __init__(self):
        super(NumberOfFieldSearchesFeature, self).__init__()

    def check(self, filter):
        return sum([1 if self.is_field_search(node) else 0 for node in filter.itertree()])


class NumberOfOptionSearchesFeature(Feature):
    
    def __init__(self):
        super(NumberOfOptionSearchesFeature, self).__init__()

    def check(self, filter):
        return sum([1 if self.is_option_search(node) else 0 for node in filter.itertree()])


class NumberOfStringSearchesFeature(Feature):
    
    def __init__(self):
        super(NumberOfStringSearchesFeature, self).__init__()

    def check(self, filter):
        return sum([1 if self.is_string_search(node) else 0 for node in filter.itertree()])


class AverageLengthOfStringSearchesFeature(Feature):
    
    def __init__(self):
        super(AverageLengthOfStringSearchesFeature, self).__init__()

    def check(self, filter):
        lengths = []
        for node in filter.itertree():
            if self.is_string_search(node):
                lengths.append(len(node.children[0].raw))
        if not lengths:
            return 0. # Should this be 0 or -1?
        return mean(lengths)


class NumberOfLogicalOperatorsFeature(Feature):
    
    def __init__(self):
        super(NumberOfLogicalOperatorsFeature, self).__init__()

    def check(self, filter):
        return sum([1 if self.is_logical_operator(node) else 0 for node in filter.itertree()])


class NumberOfTimeSearchesFeature(Feature):
    
    def __init__(self):
        super(NumberOfTimeSearchesFeature, self).__init__()

    def check(self, filter):
        return sum([1 if (self.is_time_modifier(node) or self.is_default_datetime(node)) else 0 for node in filter.itertree()])


class NumberOfSubsearchesFeature(Feature):
    
    def __init__(self):
        super(NumberOfSubsearchesFeature, self).__init__()

    def check(self, filter):
        return sum([1 if self.is_subsearch(node) else 0 for node in filter.itertree()])


class NumberOfInternalDataSearchesFeature(Feature):
    
    def __init__(self):
        super(NumberOfInternalDataSearchesFeature, self).__init__()

    def check(self, filter):
        return sum([1 if self.is_internal_data(node) else 0 for node in filter.itertree()])


class NumberOfDefaultFieldSearchesFeature(Feature):
    
    def __init__(self):
        super(NumberOfDefaultFieldSearchesFeature, self).__init__()

    def check(self, filter):
        return sum([1 if self.is_default_field(node) else 0 for node in filter.itertree()])


class NumberOfDistinctFieldsFeature(Feature):
    
    def __init__(self):
        super(NumberOfDistinctFieldsFeature, self).__init__()

    def check(self, filter):
        field_nodes = [node for node in filter.itertree() if self.is_field(node)]
        return len(set([node.raw for node in field_nodes]))


class SpecifiedCommandUsedFeature(Feature):

    def __init__(self, command):
        super(SpecifiedCommandUsedFeature, self).__init__()
        self.command = command

    def check(self, filter):
        return int(self.command == self.get_command(filter).raw)


class PositionInQueryFeature(Feature):
    
    def __init__(self):
        super(PositionInQueryFeature, self).__init__()

    def check(self, filter):
        return filter.position

class RemovesDuplicatesFeature(Feature):
    
    def __init__(self):
        super(RemovesDuplicatesFeature, self).__init__()

    def check(self, filter):
        return int(self.get_command(filter).raw in ["dedup", "uniq"])


class FiltersByPositionFeature(Feature):
    
    def __init__(self):
        super(FiltersByPositionFeature, self).__init__()

    def check(self, filter):
        return int(self.get_command(filter).raw in ["head", "tail"])


FEATURES = [
    NumberOfArgumentsFeature(),
    NumberOfWildcardMatchesFeature(),
    NumberOfConditionalsFeature(),
    NumberOfSpecificConditionalsFeature("AND"),
    NumberOfSpecificConditionalsFeature("OR"),
    NumberOfSpecificConditionalsFeature("NOT"),
    NumberOfFieldSearchesFeature(),
    NumberOfOptionSearchesFeature(),
    NumberOfStringSearchesFeature(),
    AverageLengthOfStringSearchesFeature(),
    NumberOfLogicalOperatorsFeature(),
    NumberOfLogicalOperatorsFeature(),
    NumberOfTimeSearchesFeature(),
    NumberOfSubsearchesFeature(),
    NumberOfInternalDataSearchesFeature(),
    NumberOfDefaultFieldSearchesFeature(),
    NumberOfDistinctFieldsFeature(),
    SpecifiedCommandUsedFeature("dedup"),
    SpecifiedCommandUsedFeature("head"),
    SpecifiedCommandUsedFeature("regex"),
    SpecifiedCommandUsedFeature("search"),
    SpecifiedCommandUsedFeature("tail"),
    SpecifiedCommandUsedFeature("where"),
    SpecifiedCommandUsedFeature("uniq"),
    PositionInQueryFeature(),
    RemovesDuplicatesFeature(),
    FiltersByPositionFeature()
]
