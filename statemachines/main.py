from queryutils.databases import PostgresDB, SQLite3DB
from queryutils.files import CSVFiles, JSONFiles
from graph import compute_graph, create_fsm
from paths import compute_top_paths
from os import path

ALLOWED_TYPES = ["user", "vmware:perf:", "solaris3-web-access", "path"]
MAX_PIPES = 5  # max number of pipes on path

# N: 203691
# total: 19260 versus 17085

SOURCES = {
    "csvfiles": (CSVFiles, ["path", "version"]),
    "jsonfiles": (JSONFiles, ["path", "version"]),
    "postgresdb": (PostgresDB, ["database", "user", "password"]),
    "sqlite3db": (SQLite3DB, ["srcpath"])
}

def main(type, source, querytype, output, threshold):
    edges = output + "-edges"
    if type == "path":
        if not path.isfile(edges):
            compute_graph(type, querytype, source, output)
        else:
            print "Notice: edges file named %s already exists, outputtting paths based on that." % edges
        compute_top_paths(edges, output)
    else:
        if not path.isfile(edges):
            compute_graph(type, querytype, source, output)
        else:
            print "Notice: edges file named %s already exists, drawing graph based on that." % edges
        create_fsm(output, edges, threshold)

def lookup(dictionary, lookup_keys):
    return [dictionary[k] for k in lookup_keys]

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="State machine describing transition frequency between \
                     commands of each type for unique scheduled user queries.")
    parser.add_argument("-s", "--source",
                        help="one of: " + ", ".join(SOURCES.keys()))
    parser.add_argument("-a", "--path",
                        help="the path to the data to load")
    parser.add_argument("-v", "--version", #TODO: Print possible versions 
                        help="the version of data collected")
    parser.add_argument("-U", "--user",
                        help="the user name for the Postgres database")
    parser.add_argument("-P", "--password",
                        help="the password for the Postgres database")
    parser.add_argument("-D", "--database",
                        help="the database for Postgres")
    parser.add_argument("-o", "--output",
                        help="the name of the output file")
    parser.add_argument("-t", "--type",
                        help="the type of graph to make. Options are: \
                        'user', 'vmware:perf:', 'solaris3-web-access', 'path'.")
    parser.add_argument("-r", "--threshold",
                        help="the threshold that determines which edges are drawn \
                        -- only edges with weights above this are drawn. \
                        Should be in (0.0, 1.0]")
    parser.add_argument("-q", "--querytype",
                        help="the type of queries (scheduled or interactive)")
    args = parser.parse_args()
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
