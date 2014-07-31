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

def main(source, querytype):
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

def lookup(dictionary, lookup_keys):
    return [dictionary[k] for k in lookup_keys]

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Bar graph describing how frequently commands of various \
                     types of appear in all user queries.")
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
    parser.add_argument("-q", "--querytype",
                        help="the type of queries (scheduled or interactive)")
    args = parser.parse_args()
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
