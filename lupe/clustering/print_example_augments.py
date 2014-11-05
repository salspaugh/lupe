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

def are_plur(lst, indices):
    return all([float(lst[i]) > 0. for i in indices])

def check(f, zeros, ones, bigs, plur):
    return are_zeros(f, zeros) and are_ones(f, ones) and are_bigs(f, bigs) and are_plur(f, plur)

def is_arithmetic(f):
    zeros = [3, 110]
    ones = [6, 114, 121]
    bigs = [0, 99]
    plurs = [0, 6, 20, 21, 22, 99, 100, 107, 114, 121]
    return check(f, zeros, ones, bigs, plurs)

def is_string_manipulation(f):
    zeros =  [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 90, 91, 92, 93, 94, 95, 96, 97, 98, 100, 102, 103, 104, 105, 106, 107, 109, 110, 111, 112, 113, 114, 116, 117, 118, 119, 120, 121, 123, 124, 125, 126, 127]
    ones = []
    bigs = [99]
    plurs = [20, 99]
    return check(f, zeros, ones, bigs, plurs)

def is_multivalue(f):
    zeros =  [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 48, 49, 50, 53, 54, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 100, 102, 103, 105, 106, 107, 108, 109, 111, 112, 113, 114, 116, 117, 119, 120, 121, 122, 123, 125, 126, 127]
    ones = [6, 104, 110]
    bigs = [20, 99]
    plurs = [0, 6, 20, 21, 22, 99, 104, 110]
    return check(f, zeros, ones, bigs, plurs)

def is_datetime_conversion(f):
    zeros = []
    ones = [6]
    bigs = [99]
    plurs = [0, 6, 20, 21, 22, 99, 103, 109]
    return check(f, zeros, ones, bigs, plurs)

def is_complicated(f):
    zeros = []
    ones = [3]
    bigs = [0, 21, 22, 99]
    plurs = [0, 3, 20, 21, 22, 99]
    return check(f, zeros, ones, bigs, plurs)

def is_grouping(f):
    zeros =  [1, 2, 3, 4, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127]
    ones = []
    bigs = [20, 99]
    plurs = [0, 20, 99]
    return check(f, zeros, ones, bigs, plurs)

def is_conditionals(f):
    zeros = []
    ones = [6, 24, 113]
    bigs = [0, 99]
    plurs = [0, 6, 20, 21, 22, 24, 99, 100, 101, 113]
    return check(f, zeros, ones, bigs, plurs)

def is_field_value_assignments(f):
    zeros = [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 23, 24, 25, 26, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127]
    ones = [6]
    bigs = [20, 99]
    plurs = [0, 6, 20, 99]
    return check(f, zeros, ones, bigs, plurs)

CLASSES = {
    "arithmetic": is_arithmetic,
    "string_manipulation": is_string_manipulation,
    "multivalue": is_multivalue,
    "datetime_conversion": is_datetime_conversion,
    "complicated": is_complicated,
    "grouping": is_grouping,
    "conditionals": is_conditionals,
    "field_value_assignments": is_field_value_assignments,
}

ITEMS = {
    "arithmetic": [
        "57055.0",
        "11977.4",
        "202163.2",
        "171900.4",
        "168621.0"
    ],
    "string_manipulation": [
        "119777.1",
        "127302.0",
        "36216.0",
        "37688.0",
        "110398.3",
        "202050.0",
        "202092.0",
        "202388.1",
        "171900.8"
    ],
    "multivalue": [
        "119777.2",
        "156212.2",
        "202388.2",
        "170913.4"
    ],
    "datetime_conversion": [
        "117306.0",
        "17656.0",
        "128648.2",
        "175597.0",
        "119777.5"
    ],
    "complicated": [
        "200417.1",
        "30058.0"
    ],
    "grouping": [
        "145938.1",
        "39772.8",
        "202163.0"
    ],
    "conditionals": [
        "124840.0",
        "188921.0",
        "39772.4",
        "125894.0",
        "175602.4"
    ],
    "field_value_assignments": [
        "196423.1",
        "146029.2",
        "89953.0",
        "119610.1",
        "175652.1"
    ],
}

def test_classification(features, right_answer):
    success = False
    for (cls, test) in CLASSES.iteritems():
        if test(features) and cls != right_answer:
            print "GIVEN WRONG CLASS!", cls
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

def get_plurs_indices(vectors):
    return get_indices(vectors, lambda x: x < 1)

def print_stats(ids, cls):
    features = [get_filter_features(id) for id in ids]
    features = [x[1:] for x in features if x is not None]
    print "Zeros: ", get_zeros_indices(features)
    print "Ones: ", get_ones_indices(features)
    print "Bigs: ", get_bigs_indices(features)
    print "Plurs: ", get_plurs_indices(features)
    for f in features:
        print_features(f)
        test_classification(f, cls)

for (cls, fn) in CLASSES.iteritems():
    print cls
    items = ITEMS[cls]
    print_stats(items, cls)
    print
