import lupe.statemachines.compute
import lupe.statemachines.tokens
import queryutils.arguments

MAX_PIPES = 5  # max number of pipes on path
THRESHOLD = .00001

def compute_top_paths(input, querytype, sourcetype=None):
    graph = lupe.statemachines.compute.compute_transition_graph(input, querytype, sourcetype)  
    lupe.statemachines.compute.normalize_transition_graph(graph)
    paths = get_paths(graph)
    output_paths(paths)

def get_paths(graph):
    prev = lupe.statemachines.tokens.START_TOKEN
    path = prev + ' '
    paths = {}
    generate_possible_paths(graph, prev, paths, path, 1, 0)
    return paths

def generate_possible_paths(graph, prev, paths, path, freq, count):
    if freq < THRESHOLD:
        return
    if count == MAX_PIPES - 1 or prev == lupe.statemachines.tokens.END_TOKEN:
        if prev == lupe.statemachines.tokens.END_TOKEN:
            paths[path] = freq
        return
    for curr in sorted(graph[prev], key=graph[prev].get, reverse=True):
        generate_possible_paths(graph, curr, paths, 
            path + curr + ' ', 
            freq * graph[prev][curr], 
            count + 1)

def output_paths(paths):
    for (k, v) in sorted(paths.iteritems(), key=lambda x: x[1], reverse=True):
        print k, v

if __name__ == "__main__":

    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="TODO")
    parser.add_argument("-t", "--sourcetype",
                        help="the type of graph to make. Options are: \
                        'vmware:perf:' or 'solaris3-web-access'")
    args = queryutils.arguments.get_arguments(parser)

    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if not args.source:
        raise RuntimeError("Specify the source and its arguments (-s or --source).")
    if args.querytype is None:
        raise RuntimeError("You must specify either 'interactive' or 'scheduled'.")

    source = queryutils.arguments.initialize_source(args.source, args)
    compute_top_paths(source, args.querytype, sourcetype=args.sourcetype)
