from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
from queryutils.arguments import get_arguments, lookup, SOURCES
from queryutils.parse import tokenize_query
from queryutils.query import QueryType
from queryutils.splunktypes import lookup_categories

def main(source, querytype, transformation):
    counted = defaultdict(int)
    source.connect()
    nqueries = 0
    if querytype == QueryType.INTERACTIVE:
        cursor = source.execute("SELECT text FROM queries WHERE is_interactive=true AND is_suspicious=false")
    elif querytype == QueryType.SCHEDULED:
        cursor = source.execute("SELECT DISTINCT text FROM queries WHERE is_interactive=false")
    else:
        raise RuntimeError("Invalid query type.")
    for row in cursor.fetchall():
        nqueries += 1
        query = row["text"]
        categories = lookup_categories(query)
        commands = get_commands(query)
        for (category, command) in zip(categories, commands):
            if category == transformation:
                counted[command] += 1
    total = sum(counted.values())
    counted = sorted(counted.iteritems(), key=lambda x: x[1], reverse=True)
    print "command, count"
    for (cmd, cnt) in counted:
        pct = float(cnt) / total
        print "%s, %d, %f" % (cmd, cnt, pct)
    source.close()

def get_commands(querystring):
    commands = []
    tokens = tokenize_query(querystring)
    for token in tokens:
        if token.type == "USER_DEFINED_COMMAND":
            commands.append(token.value)
        elif token.type == "MACRO":
            commands.append(token.value)
        elif token.type not in ["ARGS", "PIPE", "LBRACKET", "RBRACKET"]:
            commands.append(token.value)
    return commands

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Prints top commands for a given transformation type.")
    parser.add_argument("-t", "--transform",
                        help="the type of transformation to examine")
    args = get_arguments(parser)
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if args.source is None:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    if args.querytype is None:
        raise RuntimeError("You must specify a query type.")
    if args.transformation is None:
        raise RuntimeError("You must specify a transformation type.")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(source, args.querytype, args.transformation)
