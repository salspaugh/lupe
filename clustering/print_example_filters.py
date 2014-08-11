import json
import sys

with open(sys.argv[1]) as f:
    filter_features = json.load(f)

def get_obj_features(obj_id, feature_dict):
    for obj in feature_dict:
        if obj["id"] == obj_id:
            return obj["features"]

def get_filter_features(obj_id):
    return get_obj_features(obj_id, filter_features)

def print_features(features):
    if features is None:
        print features
        return
    s = ""
    for item in features:
        s = s + " %4.1f"
    print s % tuple([float(i) for i in features])

def are_bigs(lst, indices):
    return all([float(lst[i]) > 1. for i in indices])

def are_ones(lst, indices):
    return all([float(lst[i]) == 1. for i in indices])

def are_zeros(lst, indices):
    return all([float(lst[i]) == 0. for i in indices])

def check(f, zeros, ones, bigs):
    return are_zeros(f, zeros) and are_ones(f, ones) and are_bigs(f, bigs)

def is_macro(f):
    zeros = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26]
    ones = [1, 20]
    bigs = []
    return check(f, zeros, ones, bigs)

def is_function_based(f):
    zeros = [1, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 20, 21, 23, 25, 26]
    ones = [22]
    bigs = []
    return check(f, zeros, ones, bigs)

def is_selection(f):
    zeros = [4, 5, 7, 8, 9, 12, 13, 17, 18, 19, 21, 22, 23, 24, 25, 26]
    ones = [2, 3, 20]
    bigs = [0, 6, 10, 11, 16]
    return check(f, zeros, ones, bigs)
    return False

def is_subsearch(f):
    zeros = [4, 5, 7, 12, 17, 18, 19, 21, 22, 23, 24, 25, 26]
    ones = [13, 20]
    bigs = [0, 6, 10, 11, 16]
    return check(f, zeros, ones, bigs)

def is_disjunction(f):
    zeros = [5, 7, 12, 13, 14, 17, 18, 19, 21, 22, 23, 25, 26]
    ones = [4, 20]
    bigs = [0]
    return check(f, zeros, ones, bigs)

def is_dedup(f):
    zeros = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 18, 19, 20, 21, 22, 23, 26]
    ones = [17, 25]
    bigs = [16]
    return check(f, zeros, ones, bigs)

def is_simple_string_search(f):
    zeros = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26]
    ones = [0, 8, 20]
    bigs = [9]
    return check(f, zeros, ones, bigs)

def is_field_value_search(f):
    zeros = [4, 7, 8, 9, 12, 13, 14, 17, 18, 19, 21, 22, 23, 24, 25, 26]
    ones = [6, 15, 16, 20]
    bigs = []
    return check(f, zeros, ones, bigs)

def is_time_range_search(f):
    zeros = [1, 4, 5, 13, 14, 17, 18, 19, 21, 22, 23, 25, 26]
    ones = [2, 3, 6, 15, 16, 20]
    bigs = [0, 7, 10, 11, 12]
    return check(f, zeros, ones, bigs)

CLASSES = {
    "subsearch": is_subsearch,
    "function_based": is_function_based,
    "selection": is_selection,
    "time_range_search": is_time_range_search,
    "simple_string_search": is_simple_string_search,
    "macro": is_macro,
    "field_value_search": is_field_value_search,
    "dedup": is_dedup,
    "disjunction": is_disjunction
}

def test_classification(features, right_answer):
    success = False
    for (cls, test) in CLASSES.iteritems():
        if test(features) and cls != right_answer:
            print "GIVEN WRONG CLASS!"
        if test(features) and cls == right_answer:
            success = True
    if not success:
        print "MISSING RIGHT CLASS!"

def get_indices(vectors, fail_condition):
    indices = range(len(vectors[0]))
    for v in vectors:
        for idx, item in enumerate(v):
            if fail_condition(item) and idx in indices:
                indices.remove(idx)
    return indices

def get_zeros_indices(vectors):
    return get_indices(vectors, lambda x: x != 0)

def get_ones_indices(vectors):
    return get_indices(vectors, lambda x: x != 1)

def get_bigs_indices(vectors):
    return get_indices(vectors, lambda x: x < 2)

def print_stats(ids, cls):
    features = [get_filter_features(id) for id in ids]
    features = [x[1:] for x in features if x is not None]
    print "Zeros: ", get_zeros_indices(features)
    print "Ones: ", get_ones_indices(features)
    print "Bigs: ", get_bigs_indices(features)
    for f in features:
        print_features(f)
        test_classification(f, cls)

print "Macros:"
items = ["124777.0",
    "124703.0",
    "126165.0",
    "124779.0",
    "126241.0"]
print_stats(items, "macro")
print

print "Disjunctions:"
items = ["202564.0",
    "202689.0",
    "184636.1"]
print_stats(items, "disjunction")
print

print "Dedup:"
items = ["202163.1",
    "165345.1",
    "3801.1",
    "175652.1"]
print_stats(items, "dedup")
print

print "Field-value searches:"
items = ["163564.0",
    "40683.0"]
print_stats(items, "field_value_search")
print

print "Simple string:"
items = ["162787.0",
    "138758.0",
    "126973.0",
    "196525.1",
    "128260.0"]
print_stats(items, "simple_string_search")
print

print "Time-range searches:"
items = [
    "4390.0",
    "177964.0",
    "4741.0"]
print_stats(items, "time_range_search")
print

print "Selections:"
items = ["94570.0",
    "146387.0",
    "50086.0",
    "164727.0",
    "118597.0"]
print_stats(items, "selection")
print

print "Function-based:"
items = ["146051.1",
    "184584.0",
    "12238.1",
    "175838.0",
    "146029.1"]
print_stats(items, "function_based")
print

print "Subsearches:"
items = ["154311.0",
    "79441.0",
    "123751.0"]
print_stats(items, "subsearch")
print

