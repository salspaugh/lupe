
"""
This module featurizes only queries.

Features include:

    Done:
    - number of stages
    - how many macros are used
    - how many user-defined commands are used
    - number of non-command arguments (notion of complexity?)
    TODO:
    - number of subsearches
    - number of distinct fields referred to
    - number of times each command is used
    - number of times x comes after y for certain most common values of x and y
    - starts with x, for most common commands x
    - starts with y, for most common commands y
    - cluster that the search belongs in
    - cluster that other stages belong in
    - number of time each category of command is used (e.g., projection, filter, etc.)
    - what category of command it ends with
    - notion of complexity?

"""

class Feature(object):

    def __init__(self):
        self.versions = ["queries01"]
    
    def is_stage(self, node):
        return node.role == "STAGE" 

    def is_macro(self, node):
        return node.role == "MACRO"

    def is_user_defined_command(self, node):
        return node.role == "USER_DEFINED_COMMAND"
    
    def is_argument(self, node):
        return node.role.find("COMMAND") == -1 and node.role != "MACRO"

class NumberOfStagesFeature(Feature):
    
    def __init__(self):
        super(NumberOfStagesFeature, self).__init__()

    def check(self, parsetree):
        return sum([1 if self.is_stage(node) else 0 for node in parsetre.itertree()])


class NumberOfMacrosFeature(Feature):
    
    def __init__(self):
        super(NumberOfMacrosFeature, self).__init__()

    def check(self, parsetree):
        return sum([1 if self.is_macro(node) else 0 for node in parsetre.itertree()])
   

class NumberOfUserDefinedCommandsFeature(Feature):
    
    def __init__(self):
        super(NumberOfUserDefinedCommandsFeature, self).__init__()

    def check(self, parsetree):
        return sum([1 if self.is_user_defined_command(node) else 0 for node in parsetre.itertree()])
   

class NumberOfArgumentsFeature(Feature):
    
    def __init__(self):
        super(NumberOfArgumentsFeature, self).__init__()

    def check(self, parsetree):
        return sum([1 if self.is_argument(node) else 0 for node in parsetre.itertree()])
