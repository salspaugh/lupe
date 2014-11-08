from queryutils.arguments import get_arguments, lookup, SOURCES
from graph import compute_graph, create_fsm
from paths import compute_top_paths
from os import path

ALLOWED_TYPES = ["user", "vmware:perf:", "solaris3-web-access", "path"]
MAX_PIPES = 5  # max number of pipes on path

# N: 203691
# total: 19260 versus 17085

def main(type, source, querytype, output, threshold):
    edges = output + "-edges"
    if not path.isfile(edges):
        compute_graph_unweighted(type, querytype, source, output)
    else:
        print "Notice: edges file named %s already exists, using that." % edges
    if type == "path":
        compute_top_paths(edges, output)
    else:
        create_fsm(output, edges, threshold)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="State machine describing transition frequency between \
                     commands of each type for unique scheduled user queries.")
    parser.add_argument("-t", "--type",
                        help="the type of graph to make. Options are: \
                        'user', 'vmware:perf:', 'solaris3-web-access', 'path'.")
    parser.add_argument("-r", "--threshold",
                        help="the threshold that determines which edges are drawn \
                        -- only edges with weights above this are drawn. \
                        Should be in (0.0, 1.0]")
    args = get_arguments(parser, o=True)
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if not args.source:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    if not args.type:
        raise RuntimeError(
            "You must specify what type of state machine graph to draw.")
    if not args.type in ALLOWED_TYPES:
        raise RuntimeError(
            "Allowed types are %s" % str(ALLOWED_TYPES))
    if args.output is None:
        args.output = "%s_fsm" % args.type
    if args.threshold is None:
        args.threshold = .2
    if args.querytype is None:
        raise RuntimeError("You must specify a query type.")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(args.type, source, args.querytype, args.output, float(args.threshold))
