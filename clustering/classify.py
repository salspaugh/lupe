def are_bigs(lst, indices):
    return all([float(lst[i]) > 1. for i in indices])

def are_plur(lst, indices):
    return all([float(lst[i]) > 0. for i in indices])

def are_ones(lst, indices):
    return all([float(lst[i]) == 1. for i in indices])

def are_zeros(lst, indices):
    return all([float(lst[i]) == 0. for i in indices])

def check(f, zeros, ones, bigs, plur):
    return are_zeros(f, zeros) and are_ones(f, ones) and are_bigs(f, bigs) and are_plur(f, plur)

def is_position_based(f):
    zeros = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 22, 23, 25]
    ones = [26]
    bigs = []
    plur = []
    return check(f, zeros, ones, bigs, plur)

def is_macro(f):
    zeros = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26]
    ones = [20]
    bigs = []
    plur = []
    return check(f, zeros, ones, bigs, plur)

def is_function_based(f):
    #zeros = [1, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 20, 21, 23, 25, 26]
    zeros = []
    ones = [22]
    bigs = []
    plur = []
    return check(f, zeros, ones, bigs, plur)

def is_subsearch(f):
    zeros = [4, 5, 17, 18, 19, 21, 22, 23, 24, 25, 26]
    ones = [13, 20]
    bigs = [0, 6, 10, 11, 16]
    plur = []
    return check(f, zeros, ones, bigs, plur)

def is_selection(f):
    zeros = [4, 5, 7, 8, 9, 12, 13, 14, 17, 18, 19, 21, 22, 23, 24, 25, 26]
    ones = [0, 2, 3, 20]
    bigs = [6, 10, 11]
    plur = [15, 16]
    return check(f, zeros, ones, bigs, plur)

def is_disjunction(f):
    zeros = [13, 17, 18, 19, 21, 22, 23, 25, 26]
    ones = [20]
    bigs = [0]
    plur = [2]
    return check(f, zeros, ones, bigs, plur)

def is_field_value_search(f):
    zeros = [2, 3, 4, 5, 7, 8, 9, 13, 14, 15, 17, 18, 19, 21, 22, 23, 25, 26] # 1
    ones = [0, 6, 10, 11, 16, 20]
    bigs = []
    plur = []
    return check(f, zeros, ones, bigs, plur)

def is_dedup(f):
    #zeros = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 18, 19, 20, 21, 22, 23, 26]
    zeros = []
    ones = [17, 25]
    bigs = []
    plur = []
    return check(f, zeros, ones, bigs, plur)

def is_simple_string_search(f):
    zeros = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26]
    ones = [0, 8, 20]
    bigs = [9]
    plur = []
    return check(f, zeros, ones, bigs, plur)

def is_time_range_search(f):
    zeros = [1, 13, 14, 15, 17, 18, 19, 21, 22, 23, 25, 26]
    ones = [2, 3, 6, 16, 20]
    bigs = [0, 10, 11]
    plur = [12]
    return check(f, zeros, ones, bigs, plur)

def is_regex(f):
    zeros = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 18, 20, 21, 22, 23, 25, 26]
    ones = [16] 
    bigs = []
    plur = [24]
    return check(f, zeros, ones, bigs, plur)

FILTER_CLASSES = {
    "subsearch": is_subsearch,
    "function_based": is_function_based,
    "selection": is_selection,
    "time_range_search": is_time_range_search,
    "simple_string_search": is_simple_string_search,
    "macro": is_macro,
    "field_value_search": is_field_value_search,
    "dedup": is_dedup,
    "disjunction": is_disjunction,
    "position_based": is_position_based,
    "regex": is_regex
}

def classify(features, classes):
    if features is None:
        return "NO_FEATURES"
    classification = []
    for (c, check) in classes.iteritems():
        if check(features):
            classification.append(c)
    if len(classification) > 1:
        print classification
        return "MULTIPLE"
    if len(classification) == 0:
        return "NONE"
    return classification[0]

def is_standard(f):
    zeros = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46]
    ones = [8]
    bigs = []
    plurs = []
    return check(f, zeros, ones, bigs, plurs)

def is_top(f):
    zeros = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 46]
    ones = [10, 13, 45]
    bigs = []
    plurs = []
    return check(f, zeros, ones, bigs, plurs)

def is_by_time(f):
    zeros = [1, 2, 3, 4, 5, 7, 8, 9, 10, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46]
    ones = []
    bigs = []
    plurs = [13]
    return check(f, zeros, ones, bigs, plurs)

def is_visualize(f):
    zeros = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45]
    ones = [3, 46]
    bigs = []
    plurs = []
    return check(f, zeros, ones, bigs, plurs)

def is_visualize_time(f):
    zeros = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 45]
    ones = [0, 9, 16, 44, 46]
    bigs = []
    plurs = []
    return check(f, zeros, ones, bigs, plurs)

AGGREGATE_CLASSES = {
    "standard": is_standard,
    "top": is_top,
    "by_time": is_by_time,
    "visualize": is_visualize,
    "visualize_time": is_visualize_time,
}

if __name__ == "__main__":
    fv_features = [
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 5.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 6.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    ]
    disj_features = [
    [3.0, 1.0, 1.0, 1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 2.0, 2.0, 0.0, 0.0, 0.0, 1.0, 2.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [5.0, 0.0, 1.0, 1.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 4.0, 4.0, 0.0, 0.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [3.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 2.0, 2.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [4.0, 1.0, 1.0, 1.0, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 3.0, 3.0, 0.0, 0.0, 0.0, 1.0, 3.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    ]
    time_features = [
    [3.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 2.0, 2.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [4.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 2.0, 0.0, 0.0, 3.0, 3.0, 2.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [4.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 2.0, 0.0, 0.0, 3.0, 3.0, 2.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    ]
    for f in time_features:
        print classify(f, FILTER_CLASSES)
