import lupe.statemachines.draw
import lupe.statemachines.tokens
import queryutils.arguments
import queryutils.splunktypes

def markov_diagram(input, output, querytype, sourcetype=None, threshold=.2):
    graph = compute_transition_graph(input, querytype, sourcetype)  
    normalize_transition_graph(graph)
    lupe.statemachines.draw.make_diagram(graph, threshold, output)

def compute_transition_graph(input, querytype, sourcetype=None):
    graph = {}
    patterns = None
    count = 0
    if sourcetype is not None:
        patterns = compile_match_patterns(sourcetype)
    for query in input.get_queries(querytype):
        count += 1
        if patterns is not None and not matches(query, patterns): continue
        pipeline = lookup_transformation_pipeline(query)
        update_transition_graph(graph, pipeline)
    return graph

def compile_match_patterns(arg):
    sourcetype_match = re.compile(".*\s*(sourcetype)\s*(=)\s*['\"]?("+arg+").*['\"]?")
    source_match = re.compile(".*\s*(source)\s*(=)\s*['\"]?("+arg+").*['\"]?")
    return [sourcetype_match, source_match]

def matches(query, patterns):
    return all([p.match(query) is not None for p in patterns])

def lookup_transformation_pipeline(query):
    transformations = queryutils.splunktypes.lookup_categories(query)
    return ([lupe.statemachines.tokens.START_TOKEN] + 
        transformations + 
        [lupe.statemachines.tokens.END_TOKEN])

def update_transition_graph(graph, pipeline):
    for idx, stage in enumerate(pipeline[:-1]):
        src = stage
        dst = pipeline[idx+1]
        if not src in graph:
            graph[src] = {}
        if not dst in graph[src]:
            graph[src][dst] = 0.
        graph[src][dst] += 1.

def normalize_transition_graph(graph):
    for (src, dsts) in graph.iteritems():
        total = float(sum(dsts.values()))
        for (dst, weight) in dsts.iteritems():
            graph[src][dst] = weight*1./total

if __name__ == "__main__":

    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="State machine describing transition frequency between \
                     commands of each type for unique scheduled user queries.")
    parser.add_argument("-t", "--sourcetype",
                        help="the type of graph to make. Options are: \
                        'vmware:perf:' or 'solaris3-web-access'")
    parser.add_argument("-r", "--threshold",
                        help="the threshold that determines which edges are drawn \
                        -- only edges with weights above this are drawn. \
                        Should be in (0.0, 1.0]")
    args = queryutils.arguments.get_arguments(parser, o=True)

    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if not args.source:
        raise RuntimeError("Specify the source and its arguments (-s or --source).")
    if args.output is None:
        raise RuntimeError("Specify an output file (-o or --output).")
    if args.threshold is None:
        args.threshold = .2
    if args.querytype is None:
        raise RuntimeError("You must specify either 'interactive' or 'scheduled'.")

    source = queryutils.arguments.initialize_source(args.source, args)
    markov_diagram(source, args.output, args.querytype, 
        sourcetype=args.sourcetype, threshold=float(args.threshold))
