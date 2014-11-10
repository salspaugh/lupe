from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
from queryutils.arguments import get_arguments, lookup, SOURCES
from queryutils.parse import tokenize_query
from queryutils.query import QueryType
from queryutils.splunktypes import lookup_categories

def main(source, querytype):
    """Calculates and prints count and percentage of all sets of transformations that occur in all queries.

    :param source: where to fetch the data and arguments
    :type source: either a CSVFiles, JSONFiles, PostgresDB, or SQLite3DB
    :param querytype: type of queries to look at; either scheduled or interactive
    :type querytype: str
    """
    needs = defaultdict(int)
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
        need = list(set(categories))
        need = tuple(sorted(need))
        needs[need] += 1
    needs = sorted(needs.iteritems(), key=lambda x: x[1], reverse=True)
    print "Transformations, Count"
    for (need, cnt) in needs:
        pct = float(cnt) / float(nqueries)
        print "%s, %d, %f" % (",".join(list(need)), cnt, pct)
    source.close()

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Calculates and prints count and percentage of all sets of transformations \
                    that occur in all queries.")
    args = get_arguments(parser)
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if args.source is None:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    if args.querytype is None:
        raise RuntimeError("You must specify a query type.")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(source, args.querytype)
