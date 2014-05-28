from json import load
from Levenshtein import ratio
from os import path
from queryutils.splunktypes import lookup_category 
from scipy.stats import describe

"""
Features include:
    Done:
    - number of queries
    - number of unique queries
    - number of duplicate queries
    - number of unique templates
    - number of duplicate templates
    - number of unique skeletons
    - number of duplicate skeletons
    - number of stages
    - descriptive statistics -- number of stages per query
    - descriptive statistics -- query length
    - what stage the session ends with
    - number of distinct commands
    - descriptive statistics -- number of distinct commands per query
    - descriptive statistics -- query interarrival time
    - descriptive statistics -- similarity of each query to the last one (similarity ~ edit distance)
    - descriptive statistics -- similarity of each template to the last one (similarity ~ edit distance)
    - descriptive statistics -- similarity of each skeleton to the last one (similarity ~ edit distance)
    - whether each query is a superstring of the prior query
    - whether each query is a substring of the prior query
    - whether each template is a superstring of the prior template
    - whether each template is a substring of the prior template
    - whether each skeleton is a superstring of the prior skeleton
    - whether each skeleton is a substring of the prior skeleton
    - whether each command sequence is a superstring of the prior command sequences
    - whether each command sequence is a substring of the prior command sequences
    - whether each command category sequence is a superstring of the prior command category sequences
    - whether each command category sequence is a substring of the prior command category sequences
    - whether it ends with a visualization command
    - descriptive statistics -- rarity of commands used

"""

def read_rarity():
    thisdir = path.dirname(path.realpath(__file__))
    with open(path.join(thisdir, "rare_commands.json")) as rarity:
        return dict(load(rarity))


rarity = read_rarity()


class Feature(object):

    def __init__(self):
        self.versions = ["sessions03"]

    def is_stage(self, node):
        return node.role == "STAGE" 

    def get_commands(self, tree):
        return [node for node in tree.itertree() 
            if node.role.find("COMMAND") > -1 or node.role == "MACRO"] 
    
    def get_category(self, node):
        if node.role == "COMMAND":
            return lookup_category(node.raw)
        if node.role in ["USER_DEFINED_COMMAND", "MACRO"]:
            return node.role

    def get_categories(self, tree):
        commands = self.get_commands(tree)
        return [self.get_category(node) for node in commands]

    def get_generators(self, tree):
        roots = [node for node in tree.itertree() if node.role == "ROOT"]
        firsts = [r.children[0].children[0] for r in roots]
        return [node for node in firsts if node.raw != "search"]

class NumberOfQueriesFeature(Feature):

    def __init__(self):
        super(NumberOfQueriesFeature, self).__init__()

    def check(self, session):
        return len(session.queries)


class NumberOfUniqueQueriesFeature(Feature):

    def __init__(self):
        super(NumberOfUniqueQueriesFeature, self).__init__()

    def check(self, session):
        return len(set([query.text for query in session.queries]))


class NumberOfDuplicateQueriesFeature(Feature):

    def __init__(self):
        super(NumberOfDuplicateQueriesFeature, self).__init__()

    def check(self, session):
        nqueries = len(session.queries)
        nduplicates = len(set([query.text for query in session.queries]))
        return nqueries - nduplicates


class NumberOfUniqueTemplatesFeature(Feature):

    def __init__(self):
        super(NumberOfUniqueTemplatesFeature, self).__init__()

    def check(self, session):
        return len(set([query.parsetree.template().str_tree() 
                        for query in session.queries]))


class NumberOfDuplicateTemplatesFeature(Feature):

    def __init__(self):
        super(NumberOfDuplicateTemplatesFeature, self).__init__()

    def check(self, session):
        ntemplates = len(session.queries)
        nduplicates = len(set([query.parsetree.template().str_tree() 
                        for query in session.queries]))
        return ntemplates - nduplicates


class NumberOfUniqueSkeletonsFeature(Feature):

    def __init__(self):
        super(NumberOfUniqueSkeletonsFeature, self).__init__()

    def check(self, session):
        return len(set([query.parsetree.skeleton().str_tree() 
                        for query in session.queries]))


class NumberOfDuplicateSkeletonsFeature(Feature):

    def __init__(self):
        super(NumberOfDuplicateSkeletonsFeature, self).__init__()

    def check(self, session):
        nskeletons = len(session.queries)
        nduplicates = len(set([query.parsetree.skeleton().str_tree() 
                        for query in session.queries]))
        return nskeletons - nduplicates


class NumberOfStagesFeature(Feature):

    def __init__(self):
        super(NumberOfStagesFeature, self).__init__()

    def check(self, session):
        nstages = 0.
        for query in session.queries:
            for node in query.parsetree.itertree():
                nstages += 1. if self.is_stage(node) else 0.
        return nstages


class DescribeNumberOfStagesFeature(Feature):

    def __init__(self):
        super(DescribeNumberOfStagesFeature, self).__init__()

    def check(self, session):
        all_nstages = []
        for query in session.queries:
            nstages = 0.
            for node in query.parsetree.itertree():
                nstages += 1. if self.is_stage(node) else 0.
            all_nstages.append(nstages) 
        size, (min, max), mean, var, skew, kurt = describe(all_nstages)
        return [size, min, max, mean, var, skew, kurt]


class DescribeQueryLengthFeature(Feature):

    def __init__(self):
        super(DescribeQueryLengthFeature, self).__init__()

    def check(self, session):
        lengths = [len(query.text) for query in session.queries]
        size, (min, max), mean, var, skew, kurt = describe(lengths)
        return [size, min, max, mean, var, skew, kurt]
        

class EndsWithCategoryFeature(Feature):

    def __init__(self, category):
        super(EndsWithCategoryFeature, self).__init__()
        self.category = category

    def check(self, session):
        last_stage = None
        for node in session.queries[-1].parsetree.itertree():
            if self.is_stage(node):
                last_stage = node
        command = last_stage.children[0]
        category = self.get_category(command)
        return category == self.category


class NumberOfDistinctCommandsFeature(Feature):

    def __init__(self):
        super(NumberOfDistinctCommandsFeature, self).__init__()

    def check(self, session):
        commands = []
        for query in session.queries:
            commands += [node.raw for node in query.parsetree.itertree()]            
        return len(set(commands))


class DescribeNumberOfDistinctCommandsFeature(Feature):

    def __init__(self):
        super(DescribeNumberOfDistinctCommandsFeature, self).__init__()

    def check(self, session):
        ncommands = []
        for query in session.queries:
            ncommands.append(len(set([node.raw for node in query.parsetree.itertree()])))
        size, (min, max), mean, var, skew, kurt = describe(ncommands)
        return [size, min, max, mean, var, skew, kurt]


class DescribeInterarrivalTimesFeature(Feature):

    def __init__(self):
        super(DescribeInterarrivalTimesFeature, self).__init__()

    def check(self, session):
        times = []
        for idx, query in enumerate(session.queries[:-1]):
            curr = query.time
            next = session.queries[idx+1].time
            times.append(next - curr)
        size, (min, max), mean, var, skew, kurt = describe(times)
        return [size, min, max, mean, var, skew, kurt]


class DescribeInterQuerySimilarityFeature(Feature):

    def __init__(self):
        super(DescribeInterQuerySimilarityFeature, self).__init__()

    def check(self, session):
        ratios = []
        for idx, query in enumerate(session.queries[:-1]):
            curr = query.text
            next = session.queries[idx+1].text
            ratios.append(ratio(curr, next))
        size, (min, max), mean, var, skew, kurt = describe(ratios)
        return [size, min, max, mean, var, skew, kurt]


class QuerySuperstringFeature(Feature):

    def __init__(self):
        super(QuerySuperstringFeature, self).__init__()

    def check(self, session):
        for idx, query in enumerate(session.queries[:-1]):
            curr = query.text
            next = session.queries[idx+1].text
            if not curr in next:
                return 0.
        return 1.


class TemplateSuperstringFeature(Feature):

    def __init__(self):
        super(TemplateSuperstringFeature, self).__init__()

    def check(self, session):
        for idx, query in enumerate(session.queries[:-1]):
            curr = query.parsetree.template().str_tree()
            next = session.queries[idx+1].parsetree.template().str_tree()
            if not curr in next:
                return 0.
        return 1.


class SkeletonSuperstringFeature(Feature):

    def __init__(self):
        super(SkeletonSuperstringFeature, self).__init__()

    def check(self, session):
        for idx, query in enumerate(session.queries[:-1]):
            curr = query.parsetree.skeleton().str_tree()
            next = session.queries[idx+1].parsetree.skeleton().str_tree()
            if not curr in next:
                return 0.
        return 1.


class CommandSequenceSuperstringFeature(Feature):

    def __init__(self):
        super(CommandSequenceSuperstringFeature, self).__init__()

    def check(self, session):
        for idx, query in enumerate(session.queries[:-1]):
            curr_commands = self.get_commands(query.parsetree)
            next_commands = self.get_commands(session.queries[idx+1].parsetree)
            curr_commands = [node.raw for node in curr_commands]
            next_commands = [node.raw for node in next_commands]
            curr = " ".join(curr_commands)
            next = " ".join(next_commands)
            if not curr in next:
                return 0.
        return 1.


class CategorySequenceSuperstringFeature(Feature):

    def __init__(self):
        super(CategorySequenceSuperstringFeature, self).__init__()

    def check(self, session):
        for idx, query in enumerate(session.queries[:-1]):
            curr = query.parsetree
            next = session.queries[idx+1].parsetree
            curr_categories = self.get_categories(curr)
            next_categories = self.get_categories(next)
            curr = " ".join(curr_categories)
            next = " ".join(next_categories)
            if not curr in next:
                return 0.
        return 1.
        

class QuerySubstringFeature(Feature):

    def __init__(self):
        super(QuerySubstringFeature, self).__init__()

    def check(self, session):
        for idx, query in enumerate(session.queries[:-1]):
            curr = query.text
            next = session.queries[idx+1].text
            if not next in curr:
                return 0.
        return 1.


class TemplateSubstringFeature(Feature):

    def __init__(self):
        super(TemplateSubstringFeature, self).__init__()

    def check(self, session):
        for idx, query in enumerate(session.queries[:-1]):
            curr = query.parsetree.template().str_tree()
            next = session.queries[idx+1].parsetree.template().str_tree()
            if not next in curr:
                return 0.
        return 1.


class SkeletonSubstringFeature(Feature):

    def __init__(self):
        super(SkeletonSubstringFeature, self).__init__()

    def check(self, session):
        for idx, query in enumerate(session.queries[:-1]):
            curr = query.parsetree.skeleton().str_tree()
            next = session.queries[idx+1].parsetree.skeleton().str_tree()
            if not next in curr:
                return 0.
        return 1.


class CommandSequenceSubstringFeature(Feature):

    def __init__(self):
        super(CommandSequenceSubstringFeature, self).__init__()

    def check(self, session):
        for idx, query in enumerate(session.queries[:-1]):
            curr_commands = self.get_commands(query.parsetree)
            next_commands = self.get_commands(session.queries[idx+1].parsetree)
            curr_commands = [node.raw for node in curr_commands]
            next_commands = [node.raw for node in next_commands]
            curr = " ".join(curr_commands)
            next = " ".join(next_commands)
            if not next in curr:
                return 0.
        return 1.


class CategorySequenceSubstringFeature(Feature):

    def __init__(self):
        super(CategorySequenceSubstringFeature, self).__init__()

    def check(self, session):
        for idx, query in enumerate(session.queries[:-1]):
            curr = query.parsetree
            next = session.queries[idx+1].parsetree
            curr_categories = self.get_categories(curr)
            next_categories = self.get_categories(next)
            curr = " ".join(curr_categories)
            next = " ".join(next_categories)
            if not next in curr:
                return 0.
        return 1.


class EndsWithVisualizationFeature(Feature):

    def __init__(self):
        super(EndsWithVisualizationFeature, self).__init__()

    def check(self, session):
        visualizations = ["chart", "gauge", "timechart", "table", "xyseries"]
        last = session.queries[-1].parsetree
        commands = [command.raw for command in self.get_commands(last)]
        return commands and commands[-1] in visualizations


class NumberOfVisualizationsFeature(Feature):

    def __init__(self):
        super(NumberOfVisualizationsFeature, self).__init__()

    def check(self, session):
        visualizations = ["chart", "gauge", "timechart", "table", "xyseries"]
        count = 0.
        for query in session.queries:
            commands = [cmd.raw for cmd in self.get_commands(query.parsetree)]
            count += len([cmd for cmd in commands if cmd in visualizations])
        return count


class DescribeCommandRarityFeature(Feature):

    def __init__(self):
        super(DescribeCommandRarityFeature, self).__init__()

    def check(self, session):
        rarities = []
        for query in session.queries:
            commands = [cmd for cmd in self.get_commands(query.parsetree)]
            for cmd in commands:
                if cmd.role == "COMMAND":
                    cmd_rarity = rarity.get(cmd.raw, 0.)
                    rarities.append(cmd_rarity)
                else:
                    role_rarity = rarity.get(cmd.role, 0.)
                    rarities.append(role_rarity)
        size, (min, max), mean, var, skew, kurt = describe(rarities)
        return [size, min, max, mean, var, skew, kurt]


class NumberOfGeneratorsFeature(Feature):

    def __init__(self):
        super(NumberOfGeneratorsFeature, self).__init__()

    def check(self, session):
        return sum([len(self.get_generators(query.parsetree)) for query in session.queries])


class NumberOfSubstringQueriesOfPriorQueriesFeature(Feature):

    def __init__(self):
        super(NumberOfSubstringQueriesOfPriorQueriesFeature, self).__init__()

    def check(self, session):
        count = 0
        for i, sub in enumerate(session.queries):
            for query in session.queries[:i]:
                if sub.text in query.text:
                    count += 1
        return count


class NumberOfSuperstringQueriesOfPriorQueriesFeature(Feature):

    def __init__(self):
        super(NumberOfSuperstringQueriesOfPriorQueriesFeature, self).__init__()

    def check(self, session):
        count = 0
        for i, sup in enumerate(session.queries):
            for query in session.queries[:i]:
                if query.text in sup.text:
                    count += 1
        return count


class NumberOfSubstringTemplatesOfPriorTemplatesFeature(Feature):

    def __init__(self):
        super(NumberOfSubstringTemplatesOfPriorTemplatesFeature, self).__init__()

    def check(self, session):
        count = 0
        for i, sub in enumerate(session.queries):
            for query in session.queries[:i]:
                if sub.text in query.text:
                    count += 1
        return count


class NumberOfSuperstringTemplatesOfPriorTemplatesFeature(Feature):

    def __init__(self):
        super(NumberOfSuperstringTemplatesOfPriorTemplatesFeature, self).__init__()

    def check(self, session):
        count = 0
        for i, sup in enumerate(session.queries):
            for query in session.queries[:i]:
                if query.text in sup.text:
                    count += 1
        return count


class NumberOfSubstringSkeletonsOfPriorSkeletonsFeature(Feature):

    def __init__(self):
        super(NumberOfSubstringSkeletonsOfPriorSkeletonsFeature, self).__init__()

    def check(self, session):
        count = 0
        for i, sub in enumerate(session.queries):
            for query in session.queries[:i]:
                if sub.text in query.text:
                    count += 1
        return count


class NumberOfSuperstringSkeletonsOfPriorSkeletonsFeature(Feature):

    def __init__(self):
        super(NumberOfSuperstringSkeletonsOfPriorSkeletonsFeature, self).__init__()

    def check(self, session):
        count = 0
        for i, sup in enumerate(session.queries):
            for query in session.queries[:i]:
                if query.text in sup.text:
                    count += 1
        return count


class NumberOfSpecificCommandFeature(Feature):
    
    def __init__(self, commands):
        super(NumberOfSpecificCommandFeature, self).__init__()
        self.commands = commands

    def check(self, session):
        commands = []
        for query in session.queries:
            commands.append(self.get_commands(query.parsetree))
        commands = [cmd for cmd in commands if cmd in self.commands]
        return len(commands)


class PercentOfSpecificCommandFeature(Feature):
    
    def __init__(self, commands):
        super(PercentOfSpecificCommandFeature, self).__init__()
        self.commands = commands

    def check(self, session):
        commands = []
        for query in session.queries:
            commands.append(self.get_commands(query.parsetree))
        matching_commands = [cmd for cmd in commands if cmd in self.commands]
        if len(commands) > 0: 
            return float(len(matching_commands))/float(len(commands))
        else:
            return 0


FEATURES = [
    NumberOfQueriesFeature(),
    NumberOfUniqueQueriesFeature(),
    NumberOfDuplicateQueriesFeature(),
    NumberOfUniqueTemplatesFeature(),
    NumberOfDuplicateTemplatesFeature(),
    NumberOfUniqueSkeletonsFeature(),
    NumberOfDuplicateSkeletonsFeature(),
    NumberOfStagesFeature(),
    DescribeNumberOfStagesFeature(),
    DescribeQueryLengthFeature(),
    EndsWithCategoryFeature("InputtingSelection"),
    EndsWithCategoryFeature("Rename"),
    EndsWithCategoryFeature("FilterSelection"),
    EndsWithCategoryFeature("Join"),
    EndsWithCategoryFeature("Projection"),
    EndsWithCategoryFeature("WindowingProjection"),
    EndsWithCategoryFeature("Macro"),
    EndsWithCategoryFeature("Transpose"),
    EndsWithCategoryFeature("Miscellaneous"),
    EndsWithCategoryFeature("Aggregation"),
    EndsWithCategoryFeature("Union"),
    EndsWithCategoryFeature("Meta"),
    EndsWithCategoryFeature("ExtendedProjection"),
    EndsWithCategoryFeature("ComplexAggregation"),
    EndsWithCategoryFeature("TransformingProjection"),
    EndsWithCategoryFeature("Reorder"),
    EndsWithCategoryFeature("Cache"),
    EndsWithCategoryFeature("InputMetadata"),
    EndsWithCategoryFeature("Output"),
    EndsWithCategoryFeature("MACRO"),
    EndsWithCategoryFeature("USER_DEFINED_COMMAND"),
    NumberOfDistinctCommandsFeature(),
    DescribeNumberOfDistinctCommandsFeature(),
    #DescribeInterarrivalTimesFeature(),
    DescribeInterQuerySimilarityFeature(),
    QuerySuperstringFeature(),
    TemplateSuperstringFeature(),
    SkeletonSuperstringFeature(),
    CommandSequenceSuperstringFeature(),
    CategorySequenceSuperstringFeature(),
    QuerySubstringFeature(),
    TemplateSubstringFeature(),
    SkeletonSubstringFeature(),
    CommandSequenceSubstringFeature(),
    CategorySequenceSubstringFeature(),
    EndsWithVisualizationFeature(),
    NumberOfVisualizationsFeature(),
    DescribeCommandRarityFeature(),
    NumberOfGeneratorsFeature(),
    NumberOfSubstringQueriesOfPriorQueriesFeature(),
    NumberOfSuperstringQueriesOfPriorQueriesFeature(),
    NumberOfSubstringTemplatesOfPriorTemplatesFeature(),
    NumberOfSuperstringTemplatesOfPriorTemplatesFeature(),
    NumberOfSubstringSkeletonsOfPriorSkeletonsFeature(),
    NumberOfSuperstringSkeletonsOfPriorSkeletonsFeature(),
    NumberOfSpecificCommandFeature(["abstract"]),
    NumberOfSpecificCommandFeature(["accum"]),
    NumberOfSpecificCommandFeature(["addcoltotals"]),
    NumberOfSpecificCommandFeature(["addinfo"]),
    NumberOfSpecificCommandFeature(["addtotals"]),
    NumberOfSpecificCommandFeature(["analyzefields"]),
    NumberOfSpecificCommandFeature(["anomalies"]),
    NumberOfSpecificCommandFeature(["anomalousvalue"]),
    NumberOfSpecificCommandFeature(["append"]),
    NumberOfSpecificCommandFeature(["appendcols"]),
    NumberOfSpecificCommandFeature(["appendpipe"]),
    NumberOfSpecificCommandFeature(["arules"]),
    NumberOfSpecificCommandFeature(["associate"]),
    NumberOfSpecificCommandFeature(["audit"]),
    NumberOfSpecificCommandFeature(["autoregress"]),
    NumberOfSpecificCommandFeature(["bucket", "bin"]),
    NumberOfSpecificCommandFeature(["bucketdir"]),
    NumberOfSpecificCommandFeature(["chart"]),
    NumberOfSpecificCommandFeature(["cluster"]),
    NumberOfSpecificCommandFeature(["cofilter"]),
    NumberOfSpecificCommandFeature(["collect"]),
    NumberOfSpecificCommandFeature(["concurrency"]),
    NumberOfSpecificCommandFeature(["contingency"]),
    NumberOfSpecificCommandFeature(["convert"]),
    NumberOfSpecificCommandFeature(["correlate"]),
    NumberOfSpecificCommandFeature(["crawl"]),
    NumberOfSpecificCommandFeature(["datamodel"]),
    NumberOfSpecificCommandFeature(["dbinspect"]),
    NumberOfSpecificCommandFeature(["dedup"]),
    NumberOfSpecificCommandFeature(["delete"]),
    NumberOfSpecificCommandFeature(["delta"]),
    NumberOfSpecificCommandFeature(["diff"]),
    NumberOfSpecificCommandFeature(["erex"]),
    NumberOfSpecificCommandFeature(["eval"]),
    NumberOfSpecificCommandFeature(["eventcount"]),
    NumberOfSpecificCommandFeature(["eventstats"]),
    NumberOfSpecificCommandFeature(["extract", "kv"]),
    NumberOfSpecificCommandFeature(["fieldformat"]),
    NumberOfSpecificCommandFeature(["fields"]),
    NumberOfSpecificCommandFeature(["fieldsummary"]),
    NumberOfSpecificCommandFeature(["filldown"]),
    NumberOfSpecificCommandFeature(["fillnull"]),
    NumberOfSpecificCommandFeature(["findtypes"]),
    NumberOfSpecificCommandFeature(["folderize"]),
    NumberOfSpecificCommandFeature(["foreach"]),
    NumberOfSpecificCommandFeature(["format"]),
    NumberOfSpecificCommandFeature(["gauge"]),
    NumberOfSpecificCommandFeature(["gentimes"]),
    NumberOfSpecificCommandFeature(["geostats"]),
    NumberOfSpecificCommandFeature(["head"]),
    NumberOfSpecificCommandFeature(["highlight"]),
    NumberOfSpecificCommandFeature(["history"]),
    NumberOfSpecificCommandFeature(["iconify"]),
    NumberOfSpecificCommandFeature(["input"]),
    NumberOfSpecificCommandFeature(["inputcsv"]),
    NumberOfSpecificCommandFeature(["inputlookup"]),
    NumberOfSpecificCommandFeature(["iplocation"]),
    NumberOfSpecificCommandFeature(["join"]),
    NumberOfSpecificCommandFeature(["kmeans"]),
    NumberOfSpecificCommandFeature(["kvform"]),
    NumberOfSpecificCommandFeature(["loadjob"]),
    NumberOfSpecificCommandFeature(["localize"]),
    NumberOfSpecificCommandFeature(["localop"]),
    NumberOfSpecificCommandFeature(["lookup"]),
    NumberOfSpecificCommandFeature(["makecontinuous"]),
    NumberOfSpecificCommandFeature(["makemv"]),
    NumberOfSpecificCommandFeature(["map"]),
    NumberOfSpecificCommandFeature(["metadata"]),
    NumberOfSpecificCommandFeature(["metasearch"]),
    NumberOfSpecificCommandFeature(["multikv"]),
    NumberOfSpecificCommandFeature(["multisearch"]),
    NumberOfSpecificCommandFeature(["mvcombine"]),
    NumberOfSpecificCommandFeature(["mvexpand"]),
    NumberOfSpecificCommandFeature(["nomv"]),
    NumberOfSpecificCommandFeature(["outlier"]),
    NumberOfSpecificCommandFeature(["outputcsv"]),
    NumberOfSpecificCommandFeature(["outputlookup"]),
    NumberOfSpecificCommandFeature(["outputtext"]),
    NumberOfSpecificCommandFeature(["overlap"]),
    NumberOfSpecificCommandFeature(["pivot"]),
    NumberOfSpecificCommandFeature(["predict"]),
    NumberOfSpecificCommandFeature(["rangemap"]),
    NumberOfSpecificCommandFeature(["rare"]),
    NumberOfSpecificCommandFeature(["regex"]),
    NumberOfSpecificCommandFeature(["relevancy"]),
    NumberOfSpecificCommandFeature(["reltime"]),
    NumberOfSpecificCommandFeature(["rename"]),
    NumberOfSpecificCommandFeature(["replace"]),
    NumberOfSpecificCommandFeature(["rest"]),
    NumberOfSpecificCommandFeature(["return"]),
    NumberOfSpecificCommandFeature(["reverse"]),
    NumberOfSpecificCommandFeature(["rex"]),
    NumberOfSpecificCommandFeature(["rtorder"]),
    NumberOfSpecificCommandFeature(["run"]),
    NumberOfSpecificCommandFeature(["savedsearch"]),
    NumberOfSpecificCommandFeature(["script"]),
    NumberOfSpecificCommandFeature(["scrub"]),
    NumberOfSpecificCommandFeature(["search"]),
    NumberOfSpecificCommandFeature(["searchtxn"]),
    NumberOfSpecificCommandFeature(["selfjoin"]),
    NumberOfSpecificCommandFeature(["sendemail"]),
    NumberOfSpecificCommandFeature(["set"]),
    NumberOfSpecificCommandFeature(["setfields"]),
    NumberOfSpecificCommandFeature(["sichart"]),
    NumberOfSpecificCommandFeature(["sirare"]),
    NumberOfSpecificCommandFeature(["sistats"]),
    NumberOfSpecificCommandFeature(["sitimechart"]),
    NumberOfSpecificCommandFeature(["sitop"]),
    NumberOfSpecificCommandFeature(["sort"]),
    NumberOfSpecificCommandFeature(["spath"]),
    NumberOfSpecificCommandFeature(["stats"]),
    NumberOfSpecificCommandFeature(["strcat"]),
    NumberOfSpecificCommandFeature(["streamstats"]),
    NumberOfSpecificCommandFeature(["table"]),
    NumberOfSpecificCommandFeature(["tags"]),
    NumberOfSpecificCommandFeature(["tail"]),
    NumberOfSpecificCommandFeature(["timechart"]),
    NumberOfSpecificCommandFeature(["top"]),
    NumberOfSpecificCommandFeature(["transaction"]),
    NumberOfSpecificCommandFeature(["transpose"]),
    NumberOfSpecificCommandFeature(["trendline"]),
    NumberOfSpecificCommandFeature(["tscollect"]),
    NumberOfSpecificCommandFeature(["tstats"]),
    NumberOfSpecificCommandFeature(["typeahead"]),
    NumberOfSpecificCommandFeature(["typelearner"]),
    NumberOfSpecificCommandFeature(["typer"]),
    NumberOfSpecificCommandFeature(["uniq"]),
    NumberOfSpecificCommandFeature(["untable"]),
    NumberOfSpecificCommandFeature(["where"]),
    NumberOfSpecificCommandFeature(["x11"]),
    NumberOfSpecificCommandFeature(["xmlkv"]),
    NumberOfSpecificCommandFeature(["xmlunescape"]),
    NumberOfSpecificCommandFeature(["xpath"]),
    NumberOfSpecificCommandFeature(["xyseries"]),
    PercentOfSpecificCommandFeature(["abstract"]),
    PercentOfSpecificCommandFeature(["accum"]),
    PercentOfSpecificCommandFeature(["addcoltotals"]),
    PercentOfSpecificCommandFeature(["addinfo"]),
    PercentOfSpecificCommandFeature(["addtotals"]),
    PercentOfSpecificCommandFeature(["analyzefields"]),
    PercentOfSpecificCommandFeature(["anomalies"]),
    PercentOfSpecificCommandFeature(["anomalousvalue"]),
    PercentOfSpecificCommandFeature(["append"]),
    PercentOfSpecificCommandFeature(["appendcols"]),
    PercentOfSpecificCommandFeature(["appendpipe"]),
    PercentOfSpecificCommandFeature(["arules"]),
    PercentOfSpecificCommandFeature(["associate"]),
    PercentOfSpecificCommandFeature(["audit"]),
    PercentOfSpecificCommandFeature(["autoregress"]),
    PercentOfSpecificCommandFeature(["bucket", "bin"]),
    PercentOfSpecificCommandFeature(["bucketdir"]),
    PercentOfSpecificCommandFeature(["chart"]),
    PercentOfSpecificCommandFeature(["cluster"]),
    PercentOfSpecificCommandFeature(["cofilter"]),
    PercentOfSpecificCommandFeature(["collect"]),
    PercentOfSpecificCommandFeature(["concurrency"]),
    PercentOfSpecificCommandFeature(["contingency"]),
    PercentOfSpecificCommandFeature(["convert"]),
    PercentOfSpecificCommandFeature(["correlate"]),
    PercentOfSpecificCommandFeature(["crawl"]),
    PercentOfSpecificCommandFeature(["datamodel"]),
    PercentOfSpecificCommandFeature(["dbinspect"]),
    PercentOfSpecificCommandFeature(["dedup"]),
    PercentOfSpecificCommandFeature(["delete"]),
    PercentOfSpecificCommandFeature(["delta"]),
    PercentOfSpecificCommandFeature(["diff"]),
    PercentOfSpecificCommandFeature(["erex"]),
    PercentOfSpecificCommandFeature(["eval"]),
    PercentOfSpecificCommandFeature(["eventcount"]),
    PercentOfSpecificCommandFeature(["eventstats"]),
    PercentOfSpecificCommandFeature(["extract", "kv"]),
    PercentOfSpecificCommandFeature(["fieldformat"]),
    PercentOfSpecificCommandFeature(["fields"]),
    PercentOfSpecificCommandFeature(["fieldsummary"]),
    PercentOfSpecificCommandFeature(["filldown"]),
    PercentOfSpecificCommandFeature(["fillnull"]),
    PercentOfSpecificCommandFeature(["findtypes"]),
    PercentOfSpecificCommandFeature(["folderize"]),
    PercentOfSpecificCommandFeature(["foreach"]),
    PercentOfSpecificCommandFeature(["format"]),
    PercentOfSpecificCommandFeature(["gauge"]),
    PercentOfSpecificCommandFeature(["gentimes"]),
    PercentOfSpecificCommandFeature(["geostats"]),
    PercentOfSpecificCommandFeature(["head"]),
    PercentOfSpecificCommandFeature(["highlight"]),
    PercentOfSpecificCommandFeature(["history"]),
    PercentOfSpecificCommandFeature(["iconify"]),
    PercentOfSpecificCommandFeature(["input"]),
    PercentOfSpecificCommandFeature(["inputcsv"]),
    PercentOfSpecificCommandFeature(["inputlookup"]),
    PercentOfSpecificCommandFeature(["iplocation"]),
    PercentOfSpecificCommandFeature(["join"]),
    PercentOfSpecificCommandFeature(["kmeans"]),
    PercentOfSpecificCommandFeature(["kvform"]),
    PercentOfSpecificCommandFeature(["loadjob"]),
    PercentOfSpecificCommandFeature(["localize"]),
    PercentOfSpecificCommandFeature(["localop"]),
    PercentOfSpecificCommandFeature(["lookup"]),
    PercentOfSpecificCommandFeature(["makecontinuous"]),
    PercentOfSpecificCommandFeature(["makemv"]),
    PercentOfSpecificCommandFeature(["map"]),
    PercentOfSpecificCommandFeature(["metadata"]),
    PercentOfSpecificCommandFeature(["metasearch"]),
    PercentOfSpecificCommandFeature(["multikv"]),
    PercentOfSpecificCommandFeature(["multisearch"]),
    PercentOfSpecificCommandFeature(["mvcombine"]),
    PercentOfSpecificCommandFeature(["mvexpand"]),
    PercentOfSpecificCommandFeature(["nomv"]),
    PercentOfSpecificCommandFeature(["outlier"]),
    PercentOfSpecificCommandFeature(["outputcsv"]),
    PercentOfSpecificCommandFeature(["outputlookup"]),
    PercentOfSpecificCommandFeature(["outputtext"]),
    PercentOfSpecificCommandFeature(["overlap"]),
    PercentOfSpecificCommandFeature(["pivot"]),
    PercentOfSpecificCommandFeature(["predict"]),
    PercentOfSpecificCommandFeature(["rangemap"]),
    PercentOfSpecificCommandFeature(["rare"]),
    PercentOfSpecificCommandFeature(["regex"]),
    PercentOfSpecificCommandFeature(["relevancy"]),
    PercentOfSpecificCommandFeature(["reltime"]),
    PercentOfSpecificCommandFeature(["rename"]),
    PercentOfSpecificCommandFeature(["replace"]),
    PercentOfSpecificCommandFeature(["rest"]),
    PercentOfSpecificCommandFeature(["return"]),
    PercentOfSpecificCommandFeature(["reverse"]),
    PercentOfSpecificCommandFeature(["rex"]),
    PercentOfSpecificCommandFeature(["rtorder"]),
    PercentOfSpecificCommandFeature(["run"]),
    PercentOfSpecificCommandFeature(["savedsearch"]),
    PercentOfSpecificCommandFeature(["script"]),
    PercentOfSpecificCommandFeature(["scrub"]),
    PercentOfSpecificCommandFeature(["search"]),
    PercentOfSpecificCommandFeature(["searchtxn"]),
    PercentOfSpecificCommandFeature(["selfjoin"]),
    PercentOfSpecificCommandFeature(["sendemail"]),
    PercentOfSpecificCommandFeature(["set"]),
    PercentOfSpecificCommandFeature(["setfields"]),
    PercentOfSpecificCommandFeature(["sichart"]),
    PercentOfSpecificCommandFeature(["sirare"]),
    PercentOfSpecificCommandFeature(["sistats"]),
    PercentOfSpecificCommandFeature(["sitimechart"]),
    PercentOfSpecificCommandFeature(["sitop"]),
    PercentOfSpecificCommandFeature(["sort"]),
    PercentOfSpecificCommandFeature(["spath"]),
    PercentOfSpecificCommandFeature(["stats"]),
    PercentOfSpecificCommandFeature(["strcat"]),
    PercentOfSpecificCommandFeature(["streamstats"]),
    PercentOfSpecificCommandFeature(["table"]),
    PercentOfSpecificCommandFeature(["tags"]),
    PercentOfSpecificCommandFeature(["tail"]),
    PercentOfSpecificCommandFeature(["timechart"]),
    PercentOfSpecificCommandFeature(["top"]),
    PercentOfSpecificCommandFeature(["transaction"]),
    PercentOfSpecificCommandFeature(["transpose"]),
    PercentOfSpecificCommandFeature(["trendline"]),
    PercentOfSpecificCommandFeature(["tscollect"]),
    PercentOfSpecificCommandFeature(["tstats"]),
    PercentOfSpecificCommandFeature(["typeahead"]),
    PercentOfSpecificCommandFeature(["typelearner"]),
    PercentOfSpecificCommandFeature(["typer"]),
    PercentOfSpecificCommandFeature(["uniq"]),
    PercentOfSpecificCommandFeature(["untable"]),
    PercentOfSpecificCommandFeature(["where"]),
    PercentOfSpecificCommandFeature(["x11"]),
    PercentOfSpecificCommandFeature(["xmlkv"]),
    PercentOfSpecificCommandFeature(["xmlunescape"]),
    PercentOfSpecificCommandFeature(["xpath"]),
    PercentOfSpecificCommandFeature(["xyseries"]),
]
