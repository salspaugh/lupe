from numpy import mean

"""
This module featurizes only aggregate stages.

Features include:
    - what command is used
    - what position the command is used in
    - number of distinct fields
    - the type of data the function takes in as input
    - the type of data the function outputs
    - number of functions used
    - number of distinct functions used
    - number of times each function is used
    - deepest level of nesting
""" 

FNTYPE_GROUPS = {
    "NUMERIC_DOMAIN": ["abs", "case", "ceil", "ceiling",  "exact", "exp", "floor", "len", "ln", "log", "mvrange", "pi", "pow", "random", "round", "sigfig", "sqrt", "tonumber", "validate", "modulus", "divides", "times", "plus", "minus", "lt", "le", "ge", "gt"],
    "STRING_DOMAIN": ["case", "commands", "len", "like", "lower", "ltrim", "match", "replace", "rtrim", "searchmatch", "spath", "split", "substr", "tostring", "trim", "upper", "concat"],
    "IPADDR_DOMAIN": ["cidrmatch"],
    "TIME_DOMAIN": ["now", "relative_time", "strftime", "strptime"],
    "MV_DOMAIN": ["mvindex", "mvfilter", "mvfind", "mvjoin", "mvzip"],
    "URL_DOMAIN": ["urldecode"],
    "BOOLEAN_DOMAIN": ["and", "or", "not", "xor"],
    "NUMERIC_RANGE": ["abs", "ceil", "ceiling", "exact", "exp", "floor", "len", "ln", "log", "mvcount", "mvfind", "pi", "pow", "random", "round", "sigfig", "sqrt", "tonumber", "validate", "modulus", "divides", "times", "plus", "minus", "lt", "le", "ge", "gt"],
    "STRING_RANGE": ["commands", "exact", "lower", "ltrim", "md5", "mvjoin", "replace", "rtrim", "spath", "split", "substr", "tostring", "typeof", "trim", "upper", "validate"],
    "TIME_RANGE": ["now", "relative_time", "strftime", "strptime", "time"],
    "MV_RANGE": ["mvappend", "mvindex", "mvfilter", "mvrange", "mvzip"],
    "URL_RANGE": ["urldecode"],
    "BOOLEAN_RANGE": ["cidrmatch", "exact", "isbool", "isint", "isnotnull", "isnull", "isnum", "isstr", "like", "searchmatch", "and", "or", "not", "xor"],
    "CONDITIONAL_FUNCTIONS": ["case", "if", "ifnull"]
}

class Feature(object):

    def __init__(self):
        self.versions = ["augments01"]
    
    def is_field(self, node):
        return node.role.find("FIELD") > -1
    
    def get_command(self, tree):
        for node in tree.itertree():
            if node.role == "COMMAND": return node
    
    def is_function(self, node):
        return node.role.find("FUNCTION") > -1


class NumberOfDistinctFieldsFeature(Feature):
    
    def __init__(self):
        super(NumberOfDistinctFieldsFeature, self).__init__()

    def check(self, augment):
        field_nodes = [node for node in augment.itertree() if self.is_field(node)]
        return len(set([node.raw for node in field_nodes]))


class SpecifiedCommandUsedFeature(Feature):

    def __init__(self, command):
        super(SpecifiedCommandUsedFeature, self).__init__()
        self.command = command

    def check(self, augment):
        return int(self.command == self.get_command(augment).raw)


class PositionInQueryFeature(Feature):
    
    def __init__(self):
        super(PositionInQueryFeature, self).__init__()

    def check(self, augment):
        return augment.position


class NumberOfFunctionsFeature(Feature):
    
    def __init__(self):
        super(NumberOfFunctionsFeature, self).__init__()

    def check(self, augment):
        return len([node for node in augment.itertree() if self.is_function(node)])


class NumberOfDistinctFunctionsFeature(Feature):
    
    def __init__(self):
        super(NumberOfDistinctFunctionsFeature, self).__init__()

    def check(self, augment):
        functions = [node.raw for node in augment.itertree() if self.is_function(node)]
        return len(set(functions))


class NumberOfTimesSpecificFunctionUsedFeature(Feature):
    
    def __init__(self, function):
        super(NumberOfTimesSpecificFunctionUsedFeature, self).__init__()
        self.function = function

    def check(self, augment):
        functions = [node.raw for node in augment.itertree() if self.is_function(node)]
        functions = [fn for fn in functions if fn == self.function] # TODO: canonical function names?
        return len(functions)


class DeepestLevelOfNestingFeature(Feature):
    
    def __init__(self):
        super(DeepestLevelOfNestingFeature, self).__init__()

    def check(self, augment):
        augment.depth = 0
        max_depth = augment.depth
        stack = [augment]
        while len(stack) > 0:
            node = stack.pop(0)
            for child in node.children:
                child.depth = node.depth + 1
                max_depth = max(max_depth, child.depth)
            stack = node.children + stack
        return max_depth


class NumberSpecificTypeFunctionsFeature(Feature):
    
    def __init__(self, typekey):
        super(NumberSpecificTypeFunctionsFeature, self).__init__()
        self.typekey = typekey

    def check(self, augment):
        key_functions = FNTYPE_GROUPS[self.typekey]
        functions = [node.raw for node in augment.itertree() if self.is_function(node)]
        functions = [fn for fn in functions if fn in key_functions]
        return len(functions)


class PercentSpecificTypeFunctionsFeature(Feature):
    
    def __init__(self, typekey):
        super(PercentSpecificTypeFunctionsFeature, self).__init__()
        self.typekey = typekey

    def check(self, augment):
        key_functions = FNTYPE_GROUPS[self.typekey]
        functions = [node.raw for node in augment.itertree() if self.is_function(node)]
        matching_functions = [fn for fn in functions if fn in key_functions]
        if len(functions) > 0: 
            return float(len(matching_functions))/float(len(functions))
        else:
            return 0


FEATURES = [
    NumberOfDistinctFieldsFeature(),
    SpecifiedCommandUsedFeature("addinfo"),
    SpecifiedCommandUsedFeature("addtotals"),
    SpecifiedCommandUsedFeature("appendcols"),
    SpecifiedCommandUsedFeature("bin"),
    SpecifiedCommandUsedFeature("bucket"),
    SpecifiedCommandUsedFeature("eval"),
    SpecifiedCommandUsedFeature("eventstats"),
    SpecifiedCommandUsedFeature("extract"),
    SpecifiedCommandUsedFeature("gauge"),
    SpecifiedCommandUsedFeature("iplocation"),
    SpecifiedCommandUsedFeature("kv"),
    SpecifiedCommandUsedFeature("outputtext"),
    SpecifiedCommandUsedFeature("rangemap"),
    SpecifiedCommandUsedFeature("relevancy"),
    SpecifiedCommandUsedFeature("rex"),
    SpecifiedCommandUsedFeature("spath"),
    SpecifiedCommandUsedFeature("strcat"),
    SpecifiedCommandUsedFeature("tags"),
    SpecifiedCommandUsedFeature("xmlkv"),
    PositionInQueryFeature(),
    NumberOfFunctionsFeature(),
    NumberOfDistinctFunctionsFeature(),
    NumberOfTimesSpecificFunctionUsedFeature("abs"),
    NumberOfTimesSpecificFunctionUsedFeature("case"),
    NumberOfTimesSpecificFunctionUsedFeature("ceil"),
    NumberOfTimesSpecificFunctionUsedFeature("ceiling"),
    NumberOfTimesSpecificFunctionUsedFeature("cidrmatch"),
    NumberOfTimesSpecificFunctionUsedFeature("coalesce"),
    NumberOfTimesSpecificFunctionUsedFeature("commands"),
    NumberOfTimesSpecificFunctionUsedFeature("exact"),
    NumberOfTimesSpecificFunctionUsedFeature("exp"),
    NumberOfTimesSpecificFunctionUsedFeature("floor"),
    NumberOfTimesSpecificFunctionUsedFeature("if"),
    NumberOfTimesSpecificFunctionUsedFeature("ifnull"),
    NumberOfTimesSpecificFunctionUsedFeature("isbool"),
    NumberOfTimesSpecificFunctionUsedFeature("isint"),
    NumberOfTimesSpecificFunctionUsedFeature("isnotnull"),
    NumberOfTimesSpecificFunctionUsedFeature("isnull"),
    NumberOfTimesSpecificFunctionUsedFeature("isnum"),
    NumberOfTimesSpecificFunctionUsedFeature("isstr"),
    NumberOfTimesSpecificFunctionUsedFeature("len"),
    NumberOfTimesSpecificFunctionUsedFeature("like"),
    NumberOfTimesSpecificFunctionUsedFeature("ln"),
    NumberOfTimesSpecificFunctionUsedFeature("log"),
    NumberOfTimesSpecificFunctionUsedFeature("lower"),
    NumberOfTimesSpecificFunctionUsedFeature("ltrim"),
    NumberOfTimesSpecificFunctionUsedFeature("match"),
    NumberOfTimesSpecificFunctionUsedFeature("md5"),
    NumberOfTimesSpecificFunctionUsedFeature("mvappend"),
    NumberOfTimesSpecificFunctionUsedFeature("mvcount"),
    NumberOfTimesSpecificFunctionUsedFeature("mvindex"),
    NumberOfTimesSpecificFunctionUsedFeature("mvfilter"),
    NumberOfTimesSpecificFunctionUsedFeature("mvjoin"),
    NumberOfTimesSpecificFunctionUsedFeature("mvrange"),
    NumberOfTimesSpecificFunctionUsedFeature("mvzip"),
    NumberOfTimesSpecificFunctionUsedFeature("now"),
    NumberOfTimesSpecificFunctionUsedFeature("null"),
    NumberOfTimesSpecificFunctionUsedFeature("nullif"),
    NumberOfTimesSpecificFunctionUsedFeature("pi"),
    NumberOfTimesSpecificFunctionUsedFeature("pow"),
    NumberOfTimesSpecificFunctionUsedFeature("random"),
    NumberOfTimesSpecificFunctionUsedFeature("relative_time"),
    NumberOfTimesSpecificFunctionUsedFeature("replace"),
    NumberOfTimesSpecificFunctionUsedFeature("round"),
    NumberOfTimesSpecificFunctionUsedFeature("rtrim"),
    NumberOfTimesSpecificFunctionUsedFeature("searchmatch"),
    NumberOfTimesSpecificFunctionUsedFeature("sigfig"),
    NumberOfTimesSpecificFunctionUsedFeature("spath"),
    NumberOfTimesSpecificFunctionUsedFeature("split"),
    NumberOfTimesSpecificFunctionUsedFeature("sqrt"),
    NumberOfTimesSpecificFunctionUsedFeature("strftime"),
    NumberOfTimesSpecificFunctionUsedFeature("strptime"),
    NumberOfTimesSpecificFunctionUsedFeature("substr"),
    NumberOfTimesSpecificFunctionUsedFeature("time"),
    NumberOfTimesSpecificFunctionUsedFeature("tonumber"),
    NumberOfTimesSpecificFunctionUsedFeature("tostring"),
    NumberOfTimesSpecificFunctionUsedFeature("trim"),
    NumberOfTimesSpecificFunctionUsedFeature("typeof"),
    NumberOfTimesSpecificFunctionUsedFeature("upper"),
    NumberOfTimesSpecificFunctionUsedFeature("urldecode"),
    NumberOfTimesSpecificFunctionUsedFeature("validate"),
    NumberOfTimesSpecificFunctionUsedFeature("max"),
    NumberOfTimesSpecificFunctionUsedFeature("min"),
    NumberOfTimesSpecificFunctionUsedFeature("sum"),
    NumberOfTimesSpecificFunctionUsedFeature("and"),
    NumberOfTimesSpecificFunctionUsedFeature("or"),
    NumberOfTimesSpecificFunctionUsedFeature("not"),
    NumberOfTimesSpecificFunctionUsedFeature("xor"),
    NumberOfTimesSpecificFunctionUsedFeature("concat"),
    NumberOfTimesSpecificFunctionUsedFeature("modulus"),
    NumberOfTimesSpecificFunctionUsedFeature("divides"),
    NumberOfTimesSpecificFunctionUsedFeature("times"),
    NumberOfTimesSpecificFunctionUsedFeature("plus"),
    NumberOfTimesSpecificFunctionUsedFeature("minus"),
    NumberOfTimesSpecificFunctionUsedFeature("lt"),
    NumberOfTimesSpecificFunctionUsedFeature("le"),
    NumberOfTimesSpecificFunctionUsedFeature("ge"),
    NumberOfTimesSpecificFunctionUsedFeature("gt"),
    DeepestLevelOfNestingFeature(),
    NumberSpecificTypeFunctionsFeature("NUMERIC_DOMAIN"),
    NumberSpecificTypeFunctionsFeature("STRING_DOMAIN"),
    NumberSpecificTypeFunctionsFeature("IPADDR_DOMAIN"),
    NumberSpecificTypeFunctionsFeature("TIME_DOMAIN"),
    NumberSpecificTypeFunctionsFeature("MV_DOMAIN"),
    NumberSpecificTypeFunctionsFeature("URL_DOMAIN"),
    NumberSpecificTypeFunctionsFeature("BOOLEAN_DOMAIN"),
    NumberSpecificTypeFunctionsFeature("NUMERIC_RANGE"),
    NumberSpecificTypeFunctionsFeature("STRING_RANGE"),
    NumberSpecificTypeFunctionsFeature("TIME_RANGE"),
    NumberSpecificTypeFunctionsFeature("MV_RANGE"),
    NumberSpecificTypeFunctionsFeature("URL_RANGE"),
    NumberSpecificTypeFunctionsFeature("BOOLEAN_RANGE"),
    NumberSpecificTypeFunctionsFeature("CONDITIONAL_FUNCTIONS"),
    PercentSpecificTypeFunctionsFeature("NUMERIC_DOMAIN"),
    PercentSpecificTypeFunctionsFeature("STRING_DOMAIN"),
    PercentSpecificTypeFunctionsFeature("IPADDR_DOMAIN"),
    PercentSpecificTypeFunctionsFeature("TIME_DOMAIN"),
    PercentSpecificTypeFunctionsFeature("MV_DOMAIN"),
    PercentSpecificTypeFunctionsFeature("URL_DOMAIN"),
    PercentSpecificTypeFunctionsFeature("BOOLEAN_DOMAIN"),
    PercentSpecificTypeFunctionsFeature("NUMERIC_RANGE"),
    PercentSpecificTypeFunctionsFeature("STRING_RANGE"),
    PercentSpecificTypeFunctionsFeature("TIME_RANGE"),
    PercentSpecificTypeFunctionsFeature("MV_RANGE"),
    PercentSpecificTypeFunctionsFeature("URL_RANGE"),
    PercentSpecificTypeFunctionsFeature("BOOLEAN_RANGE"),
    PercentSpecificTypeFunctionsFeature("CONDITIONAL_FUNCTIONS")
]
    
