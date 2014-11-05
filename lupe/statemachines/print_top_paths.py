
import operator

PARSE_DIR = 'results/fix_adhoc/relations_bigram_heatmaps/user_weighted/'
RESULTS_DIR = 'results/fix_adhoc/top_paths/user_weighted/'
THRESHOLD = .001
MAX_PIPES = 5  # max number of pipes on path
QUERY_TYPES = ['unique_adhoc','unique_scheduled']


def get_paths():
    prev = '<start>'
    path = prev + ' '
    paths = {}
    generate_possible_paths(prev, paths, path, 1, 0)
    return paths


def generate_possible_paths(prev, paths, path, freq, count):
    if freq < THRESHOLD:
        return
    if count == MAX_PIPES - 1 or prev == "<end>":
        if prev == "<end>":
            paths[path] = freq
        return
    for curr in sorted(gramtab[prev], key=gramtab[prev].get, reverse=True):
        generate_possible_paths(curr, paths,
                                path + curr + ' ', freq * gramtab[prev][curr], count + 1)


def write_top_paths(paths, query):
    with open(RESULTS_DIR + query +
              '-' + str(THRESHOLD) + ".txt", 'w') as f:
        for path in sorted(paths, key=paths.get, reverse=True):
            f.write(path + ": " + str(paths[path]) + '\n')


for query in QUERY_TYPES:
    gramtab = {}
    with open(PARSE_DIR + query + ".txt", 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) != 4:
                continue
            else:
                first = parts[0]
                second = parts[1]
                freq = float(parts[3])
                if first not in gramtab:
                    gramtab[first] = {}
                if second not in gramtab[first]:
                    gramtab[first][second] = freq
    paths = get_paths()
    write_top_paths(paths, query)
