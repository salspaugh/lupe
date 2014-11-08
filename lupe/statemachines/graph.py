from fsm import State, FiniteStateMachine, get_graph
from json import load, dump
from queryutils.splunktypes import lookup_categories
from queryutils.query import QueryType
import re

START_TOKEN = "<start>"  # token you want to represent as start of query
END_TOKEN = "<end>"  # token you want to represent as end of query
THRESHOLD = 0.2  # Change to 0 if you want to show all edges
EDGE_FORMAT = "{:.2f}"

def compute_graph(type, querytype, source, output):
    graph = {}
    distinct = set()
    ntotal = nincluded = nusers = 0.
    #for (uid, text) in source.get_uid_with_text(interactive=(type == QueryType.INTERACTIVE)):
    distinct_queries = open("%s-distinct-queries.txt" % output, "w")
    for user in source.get_users_with_queries():
        print "Getting data for user " + str(user.name) + "..."
        if querytype == QueryType.INTERACTIVE:
            if user.user_type == "suspicious": continue
            queries = [q.text for q in user.interactive_queries
                if not q.is_suspicious]
        elif querytype == QueryType.SCHEDULED:
            queries = set([q.text for q in user.noninteractive_queries])
        else:
            raise RuntimeError("Invalid query type.")
        if type != "user":
            queries = filter_queries_of_source(type, queries)
        ntotal += len(user.queries)
        nincluded += len(queries)
        distinct = distinct.union(queries)
        for query in queries:
            distinct_queries.write(query)
            distinct_queries.write("\n")
        user_graph = compute_user_graph(queries)
        for first in user_graph:
            for second in user_graph[first]:
                edge = (first, second)
                if edge not in graph:
                    graph[edge] = 0.
                graph[edge] += lookup_edge(first, second, user_graph)
        if type != "user" and len(user_graph) > 0:
            nusers += 1.
        elif type == "user":
            nusers += 1
        print "next user...\n"
    graph = {k: v / nusers for k, v in graph.items()}
    print "NUMBER DISTINCT QUERIES: %d" % len(distinct)
    output_graph_data(graph, output + "-edges", nincluded, ntotal)
    distinct_queries.close()

def fetch_queries(source, query_type):
    source.connect()
    if query_type == QueryType.INTERACTIVE:
        sql = "SELECT text FROM queries, users \
                WHERE queries.user_id=users.id AND \
                    is_interactive=true AND \
                    is_suspicious=false AND \
                    user_type is null"
    elif query_type == QueryType.SCHEDULED:
        sql = "SELECT DISTINCT text FROM queries WHERE is_interactive=false"
    else:
        raise RuntimeError("Invalid query type.")
    cursor = source.execute(sql)
    for row in cursor.fetchall():
        yield row["text"]
    source.close()

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
        data["title"] = "%d distinct queries" % int(proportion)
    else:
        fraction = proportion / total
        data["title"] = "{0:.2f}% of queries".format(float(fraction) * 100)
    data["edges"] = []
    for edge in sorted(graph, key=graph.get, reverse=True):
        data["edges"].append([edge] + [graph[edge]])
    with open(output, 'w') as f:
        dump(data, f, indent=4, separators=(',', ': '))

def create_fsm(label, datafilename, threshold=THRESHOLD):
    fsm = FiniteStateMachine('Query Relations')
    states = {
        "<start>": State('Start', initial=True),
        "Aggregate": State('Aggregate'),
        "Cache": State('Cache'),
        "Augment":  State('Augment'),
        "Filter": State('Filter'),
        "Read Metadata": State(r'Read\nMetadata'),
        "Input": State('Input'),
        "Join": State('Join'),
        "Macro": State('Macro'),
        "Meta": State('Meta'),
        "Miscellaneous": State('Misc'),
        "Output": State('Output'),
        "Project": State('Project'),
        "Rename": State('Rename'),
        "Reorder": State('Reorder'),
        "External": State(r'External'),
        "Transform": State('Transform'),
        "Transpose": State('Transpose'),
        "Set": State('Set'),
        "Window": State('Window'),
        "<end>": State('End')
    }

    remaining_dsts = ['Aggregate', 'Cache', 'Augment', "Filter",
             "Input", "Join", 'Macro', 'Meta', "Miscellaneous", 'Output',
             "Project", 'Read Metadata', 'Rename', 'Reorder', 'External', "Transform",
             'Transpose', 'Set', 'Window']
    remaining_srcs = ['Aggregate', 'Cache', 'Augment', "Filter",
             "Input", "Join", 'Macro', 'Meta', "Miscellaneous", 'Output',
             "Project", 'Read Metadata', 'Rename', 'Reorder', 'External', "Transform",
             'Transpose', 'Set', 'Window']

    graph_data = read_graph_data(datafilename)

    title = graph_data["title"]
    title = State(title)

    edges = graph_data["edges"]
    # Add edges that are heavier than the threshold.
    for (edge, weight) in edges:
        if weight < threshold: break
        weight = EDGE_FORMAT.format(weight)
        (src, dst) = edge
        if src in remaining_srcs and src != dst:
            remaining_srcs.remove(src)
        if dst in remaining_dsts and src != dst:
            remaining_dsts.remove(dst)
        states[src][(tuple(edge), weight)] = states[dst]

    # Make sure all nodes have at least one ingoing and outgoing edge.
    for (edge, weight) in edges:
        (src, dst) = edge
        found = False
        if src in remaining_srcs and src != dst:
            remaining_srcs.remove(src)
            found = True
        if dst in remaining_dsts and src != dst:
            remaining_dsts.remove(dst)
            found = True
        if found:
            weight = EDGE_FORMAT.format(float(weight))
            states[src][(tuple(edge), weight)] = states[dst]

    missing = []
    for state in remaining_dsts:
        missing.append(states[state].name)

    filename = "%s-%s.pdf" % (label, str(threshold))
    #get_graph(fsm, title=title, missing=missing).draw(filename, prog='dot')
    get_graph(fsm, title=False, missing=missing).draw(filename, prog='dot')

def read_graph_data(filename):
    with open(filename) as f:
        return load(f)