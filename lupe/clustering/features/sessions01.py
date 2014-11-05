from queryutils.parse import parse_query
import re


class Feature(object):

    def __init__(self):
        self.versions = ["features01"]


class StringAppearsAtLeastOnceFeature(Feature):

    def __init__(self, searchstr):
        super(StringAppearsAtLeastOnceFeature, self).__init__()
        self.searchstr = searchstr.lower()

    def check(self, session):
        for query in session.queries:
            if query.text.lower().find(self.searchstr) > -1:
                return 1
        return 0


class UsesOnlySearchFeature(Feature):

    def __init__(self):
        super(UsesOnlySearchFeature, self).__init__()

    @classmethod
    def check(self, session):
        count = 0
        for query in session.queries:
            parse = parse_query(query)
            if type(parse) == None:
                raise NameError("cannot parse")
            if parse != None:
                for elem in parse.itertree():
                    if elem.role == 'COMMAND' and elem.raw != 'search':
                        return 0
        return 1


class UsesSimpleSearchFeature(Feature):

    def __init__(self):
        super(UsesSimpleSearchFeature, self).__init__()

    @classmethod
    def check(self, session):
        for query in session.queries:
            if type(parse_query(query)) == None:
                raise Exception("cannot parse")
            if parse_query(query) != None:
                parse = parse_query(query).str_tree()
                if parse != None:
                    parse_list = parse.split('\n')
                    if len(parse_list) != 5 or ("('COMMAND': 'search')" not in parse):
                        return 0
        return 1

# Selects from source / sourcetype / host only


class UsesCertainSearchFeature(Feature):

    def __init__(self):
        super(UsesCertainSearchFeature, self).__init__()

    @classmethod
    def check(self, session):
        for query in session.queries:
            parse = parse_query(query)
            if type(parse_query(query)) == None:
                raise Exception("cannot parse")
            if parse != None:
                for elem in parse.itertree():
                    if elem.role == 'DEFAULT_FIELD' and (elem.raw != 'host' and elem.raw != 'source' and elem.raw != 'sourcetype'):
                        return 0
        return 1


class UsesBrowsingDifferentFeature(Feature):

    def __init__(self):
        super(UsesBrowsingDifferentFeature, self).__init__()

    @classmethod
    def check(self, session):
        source_list = []
        for query in session.queries:
            parse = query.text
            if parse != None:
                if 'source=' in parse:
                    source = re.findall(
                        r'(?:"[^"]*")' + r"|(?:'[^']*')", parse)
                    if source != []:
                        if source in source_list:
                            return 0
                        source_list.append(source)
        return 1

FEATURES = [
    StringAppearsAtLeastOnceFeature("timechart"),
    StringAppearsAtLeastOnceFeature("groupby"),
    StringAppearsAtLeastOnceFeature("rename"),
    StringAppearsAtLeastOnceFeature("rex"),
    StringAppearsAtLeastOnceFeature("top"),
    StringAppearsAtLeastOnceFeature("stats"),
    StringAppearsAtLeastOnceFeature("eval"),
    UsesOnlySearchFeature(),
    UsesSimpleSearchFeature(),
    UsesCertainSearchFeature(),
    UsesBrowsingDifferentFeature()
]
