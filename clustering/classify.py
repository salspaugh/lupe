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

def is_macro(f):
    zeros = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26]
    ones = [1, 20]
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

def is_selection(f):
    zeros = [4, 5, 7, 8, 9, 12, 13, 17, 18, 19, 21, 22, 23, 24, 25, 26]
    ones = [2, 3, 20]
    bigs = [0, 6, 10, 11, 16]
    plur = []
    return check(f, zeros, ones, bigs, plur)

def is_subsearch(f):
    zeros = [4, 5, 7, 12, 17, 18, 19, 21, 22, 23, 24, 25, 26]
    ones = [13, 20]
    bigs = [0, 6, 10, 11, 16]
    plur = []
    return check(f, zeros, ones, bigs, plur)

def is_disjunction(f):
    zeros = [7, 12, 13, 14, 17, 18, 19, 21, 22, 23, 25, 26]
    ones = [20]
    bigs = [0]
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

def is_field_value_search(f):
    zeros = [3, 4, 5, 8, 9, 13, 14, 17, 18, 19, 21, 22, 23, 25, 26]
    ones = [6, 16, 20]
    bigs = []
    plur = []
    return check(f, zeros, ones, bigs, plur)

def is_time_range_search(f):
    zeros = [1, 4, 5, 13, 14, 17, 18, 19, 21, 22, 23, 25, 26]
    ones = [2, 3, 6, 15, 16, 20]
    bigs = [0, 7, 10, 11, 12]
    plur = []
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
    "disjunction": is_disjunction
}
