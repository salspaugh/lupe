from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
from queryutils.databases import PostgresDB, SQLite3DB
from queryutils.files import CSVFiles, JSONFiles
from queryutils.parse import tokenize_query
from queryutils.splunktypes import lookup_categories

SOURCES = {
    "postgresdb": (PostgresDB, ["database", "user", "password"]),
    "sqlite3db": (SQLite3DB, ["srcpath"])
}

class QueryType(object):
    INTERACTIVE = "interactive"
    SCHEDULED = "scheduled"

def main(source, querytype, output):
    stages_counts, stages_commands_count, queries_counts, queries_commands_count, nqueries = tally_stages_counts(source, querytype)
    print_tranformation_command_percents(stages_commands_count, queries_commands_count)
    print "Number of Filter stages: %d" % stages_counts["Filter"]
    print "Number of Augment stages: %d" % stages_counts["Augment"]
    print "Number of Aggregate stages: %d" % stages_counts["Aggregate"]
    create_histogram(stages_counts, queries_counts, nqueries, output)

def tally_stages_counts(source, querytype):
    # TODO: FIXME: Fix this terribly designed function!
    stages_counts = defaultdict(int)
    stages_commands_count = defaultdict(dict)
    queries_counts = defaultdict(int)
    queries_commands_count = defaultdict(dict)
    nqueries = 0
    source.connect()
    if querytype == QueryType.INTERACTIVE:
        cursor = source.execute("SELECT text FROM queries WHERE is_interactive=true AND is_suspicious=false") 
    elif querytype == QueryType.SCHEDULED:
        cursor = source.execute("SELECT DISTINCT text FROM queries WHERE is_interactive=false") 
    else:
        raise RuntimeError("Invalid query type.")
    for row in cursor.fetchall():
        query = row["text"]
        categories = lookup_categories(query)
        commands = lookup_commands(query)
        if len(categories) > 0:
            nqueries += 1
            for category, command in zip(categories, commands):
                stages_counts[category] += 1
                if not command in stages_commands_count[category]:
                    stages_commands_count[category][command] = 0
                stages_commands_count[category][command] += 1
            for category in set(categories):
                queries_counts[category] += 1
                if not command in queries_commands_count[category]:
                    queries_commands_count[category][command] = 0
                queries_commands_count[category][command] += 1
    source.close()
    return stages_counts, stages_commands_count, queries_counts, queries_commands_count, nqueries

def lookup_commands(querystring):
    commands = []
    tokens = tokenize_query(querystring)
    for token in tokens:
        val = token.value.strip().lower()
        if token.type == "EXTERNAL_COMMAND":
            commands.append(val)
        elif token.type == "MACRO":
            commands.append(val)
        elif token.type not in ["ARGS", "PIPE", "LBRACKET", "RBRACKET"]:
            commands.append(val)
    return commands

def print_tranformation_command_percents(stages_commands_count, queries_commands_count):
    print "Stages: "
    for (transformation, commands) in stages_commands_count.iteritems():
        print "\t%s" % transformation
        total = float(sum(commands.values()))
        commands = sorted(commands.iteritems(), key=lambda x: x[1], reverse=True)
        for (cmd, cnt) in commands:
            pct = float(cnt) / total
            print "\t\t%50s\t%7d\t%8f" % (cmd, cnt, pct)
    print "Queries: "
    for (transformation, commands) in queries_commands_count.iteritems():
        print "\t%s" % transformation
        total = float(sum(commands.values()))
        commands = sorted(commands.iteritems(), key=lambda x: x[1], reverse=True)
        for (cmd, cnt) in commands:
            pct = float(cnt) / total
            print "\t\t%50s\t%7d\t%8f" % (cmd, cnt, pct)


def create_histogram(stages_per_transformation, queries_per_transformation, nqueries, output):
    nstages = float(sum(stages_per_transformation.values()))
    nqueries = float(nqueries)

    spcts = { k: v/nstages*100 for (k,v) in stages_per_transformation.iteritems() }
    qpcts = { k: v/nqueries*100 for (k,v) in queries_per_transformation.iteritems() }
    spcts = sorted(spcts.iteritems(), key=lambda x: x[1], reverse=True)
    names = [k for (k,v) in spcts]
    qpcts = [qpcts[k] for (k,v) in spcts]
    spcts = [v for (k,v) in spcts]

    #fig = plt.figure(figsize=(13.5, 8.0))
    index = np.arange(len(stages_per_transformation))

    print "transformation, % stages, % queries"
    for (n, s, q) in zip(names, spcts, qpcts):
        print "%s, %f, %f" % (n, s, q)
    
    plt.subplot(2, 1, 1)
    plt.bar(index, spcts, 1, color="r")
    plt.ylabel("% stages", fontsize=18)
    plt.yticks(range(0, 100, 10), fontsize=12)
    plt.xticks(index + 0.5, ["" for n in names])
    plt.text(12, 72, "N = " + str(int(nstages)) + " stages",
        fontsize=16, bbox=dict(facecolor="none", edgecolor="black", pad=10.0))
    plt.tick_params(bottom="off")
    
    plt.subplot(2, 1, 2)
    plt.bar(index, qpcts, 1, color="c")
    plt.ylabel("% queries", fontsize=18)
    plt.yticks(range(0, 100, 10), fontsize=12)
    plt.xticks(index + 0.5, names, rotation=-45, fontsize=16,
       rotation_mode="anchor", ha="left")
    #plt.xlabel("Transformation Type", fontsize=20)
    plt.text(12, 80, "N = " + str(int(nqueries)) + " queries",
             fontsize=16, bbox=dict(facecolor="none", edgecolor="black", pad=10.0))
    plt.tick_params(bottom="off")

    plt.autoscale(enable=True, axis="x", tight=None)
    plt.tight_layout()
    plt.savefig(output + ".pdf", dpi=400)

def lookup(dictionary, lookup_keys):
    return [dictionary[k] for k in lookup_keys]

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Bar graph describing how frequently each transformation appears in user queries.")
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
    parser.add_argument("-q", "--querytype",
                        help="the type of queries (scheduled or interactive)")
    args = parser.parse_args()
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if args.source is None:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    if args.output is None:
        args.output = "categories_histogram"
    if args.querytype is None:
        raise RuntimeError("You must specify a query type.")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(source, args.querytype, args.output)
