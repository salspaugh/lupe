from queryutils.databases import PostgresDB, SQLite3DB
from queryutils.files import CSVFiles, JSONFiles
from queryutils.splunktypes import lookup_categories
from graph import create_fsm
from json import dump
from os import path
import re

START_TOKEN = "<start>"  # token you want to represent as start of query
END_TOKEN = "<end>"  # token you want to represent as end of query
ALLOWED_TYPES = ["user", "vmware:perf:", "solaris3-web-access"]

# N: 203691
# total: 19260 versus 17085

SOURCES = {
    "csvfiles": (CSVFiles, ["path", "version"]),
    "jsonfiles": (JSONFiles, ["path", "version"]),
    "postgresdb": (PostgresDB, ["database", "user", "password"]),
    "sqlite3db": (SQLite3DB, ["srcpath"])
}

def main(type, source, output):
    edges = output + "-edges"
    if not path.isfile(edges):
        compute_graph(type, source, output)
    else:
        print "Notice: edges file named %s already exists, drawing graph based on that." % edges
    create_fsm(output, edges)

def compute_graph(type, source, output): 
    graph = {}
    ntotal = nincluded = nusers = 0.
    for user in source.get_users_with_queries():
        print "Getting data for user " + str(user.name) + "..."
        queries = set([q.text for q in user.noninteractive_queries])
        if type != "user":
            queries = filter_queries_of_source(type, queries)
        ntotal += len(user.queries)
        nincluded += len(queries)
        user_graph = compute_user_graph(queries)
        for first in user_graph:
            for second in user_graph[first]:
                edge = (first, second)
                if edge not in graph:
                    graph[edge] = 0.
                graph[edge] += lookup_edge(first, second, user_graph)
        nusers += 1.
        print "ntotalext user...\n"
    graph = {k: v / nusers for k, v in graph.items()}
    output_graph_data(graph, output + "-edges", nincluded, ntotal)

def filter_queries_of_source(source, queries): # TODO: Test this.
    filtered = []
    st = re.compile(".*\s*(sourcetype)\s*(=)\s*['\"]?("+source+").*['\"]?")
    s = re.compile(".*\s*(source)\s*(=)\s*['\"]?("+source+").*['\"]?")
    for query in queries:
        if st.match(query) or s.match(query):
            filtered.append(query)
    return filtered

def compute_user_graph(queries):
    graph = {}
    for query in queries:
        graph = tally_completions(query, graph)
    return graph

def tally_completions(query, graph):
    categories = lookup_categories(query)
    if categories != []:
        categories = [START_TOKEN] + categories + [END_TOKEN]
        for i, first in enumerate(categories[:-1]):
            second = categories[i+1]
            if not first in graph:
                graph[first] = {}
            if not second in graph[first]:
                graph[first][second] = 0
            graph[first][second] += 1
    return graph

def lookup_edge(node1, node2, table):
    if table.get(node1) and table.get(node1).get(node2):
        counts = table.get(node1)
        total = float(sum(counts.values()))
        percent = table.get(node1).get(node2) / total
        # if percent >= THRESHOLD:
        #     print node1 + ": " + node2
        return percent
    return 0

def output_graph_data(graph, output, proportion, total):
    data = {}
    if proportion < 500:
        data["title"] = "%d queries" % int(proportion)
    else:
        fraction = proportion / total
        data["title"] = "{0:.2f}% of queries".format(float(fraction) * 100)
    data["edges"] = []
    for edge in sorted(graph, key=graph.get, reverse=True):
        data["edges"].append([edge] + [graph[edge]])
    with open(output, 'w') as f:
        dump(data, f, indent=4, separators=(',', ': '))


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
                        'user', 'vmware:perf:', 'solaris3-web-access'.")
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
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(args.type, source, args.output)
