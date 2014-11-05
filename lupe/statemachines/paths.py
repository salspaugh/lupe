from json import dump
from graph import read_graph_data

MAX_PIPES = 5  # max number of pipes on path
THRESHOLD = .001

def compute_top_paths(edges, output):
    graph = {}
    graph_data = read_graph_data(edges)
    for (edge, weight) in graph_data["edges"]:
        (src, dst) = edge
        if not src in graph:
            graph[src] = {}
        if not dst in graph[src]:
            graph[src][dst] = weight
    paths = get_paths(graph)
    write_top_paths(paths, output)

def get_paths(graph):
    prev = '<start>'
    path = prev + ' '
    paths = {}
    generate_possible_paths(graph, prev, paths, path, 1, 0)
    return paths


def generate_possible_paths(graph, prev, paths, path, freq, count):
    if freq < THRESHOLD:
        return
    if count == MAX_PIPES - 1 or prev == "<end>":
        if prev == "<end>":
            paths[path] = freq
        return
    for curr in sorted(graph[prev], key=graph[prev].get, reverse=True):
        generate_possible_paths(graph, curr, paths, path + curr + ' ', freq * graph[prev][curr], count + 1)

def write_top_paths(paths, output):
    output = "%s-paths" % output
    with open(output, 'w') as f:
        paths = sorted(paths, key=paths.get, reverse=True)
        dump(paths, f, indent=4, separators=(',', ': '))
