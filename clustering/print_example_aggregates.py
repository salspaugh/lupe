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

def is_standard(f):
    zeros = []
    ones = []
    bigs = []
    return check(f, zeros, ones, bigs)

def is_top(f):
    zeros = []
    ones = []
    bigs = []
    return check(f, zeros, ones, bigs)

def is_by_time(f):
    zeros = []
    ones = []
    bigs = []
    return check(f, zeros, ones, bigs)

def is_visualize(f):
    zeros = []
    ones = []
    bigs = []
    return check(f, zeros, ones, bigs)

def is_visualize_time(f):
    zeros = []
    ones = []
    bigs = []
    return check(f, zeros, ones, bigs)

CLASSES = {
    "standard": is_standard,
    "top": is_top,
    "by_time": is_by_time,
    "visualize": is_visualize,
    "visualize_time": is_visualize_time,
}

ITEMS = {
    "standard": [
        "127028.0",
        "168703.0",
        "196368.0",
        "131892.0",
        "146051.0"],
    "top": [
        "145023.0",
        "202446.0",
        "52750.0",
        "145628.0",
        "120343.0"],
    "by_time": [
        "162897.0",
        "202383.2"],
    "visualize": [
        "127302.0",
        "127041.0",
        "54865.0",
        "163371.0",
        "146016.0"],
    "visualize_time": [
        "127060.0",
        "123655.0",
        "80982.0",
        "176492.0",
        "49991.0"]
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

for (cls, fn) in CLASSES.iteritems():
    print cls
    items = ITEMS[cls]
    print_stats(items, cls)
    print
