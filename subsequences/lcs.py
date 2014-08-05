from collections import defaultdict
from queryutils.databases import PostgresDB, SQLite3DB
from queryutils.files import CSVFiles, JSONFiles
from queryutils.splunktypes import lookup_categories
import csv

SOURCES = {
    "csvfiles": (CSVFiles, ["path", "version"]),
    "jsonfiles": (JSONFiles, ["path", "version"]),
    "postgresdb": (PostgresDB, ["database", "user", "password"]),
    "sqlite3db": (SQLite3DB, ["srcpath"])
}

MIN_LEN = 2
MAX_LEN = 6

class QueryType(object):
    INTERACTIVE = "interactive"
    SCHEDULED = "scheduled"

def longest_common_subsequences(source, querytype, output):
    nusers = nqueries = 0.
    sequences = defaultdict(int)
    for user in source.get_users_with_queries():
        if querytype == QueryType.INTERACTIVE:
            queries = [q for q in user.interactive_queries 
                if not q.is_suspicious]
        elif querytype == QueryType.SCHEDULED:
            queries = set([q.text for q in user.noninteractive_queries])
        else:
            raise runtimeerror("invalid query type.")
        nqueries += len(queries)
        for query in queries: # TODO: Filter out bad queries?
            categories = lookup_categories(query)
            for length in range(MIN_LEN, MAX_LEN+1):
                for idx, item in enumerate(categories[:-length+1]):
                    sequence = tuple([length] + categories[idx:idx+length])
                    sequences[sequence] += 1.
        nusers += 1.
    sequences = { k: v / nusers for k, v in sequences.items()}
    write_sequences(sequences, output, nqueries)
    
def write_sequences(sequences, output, total):
    with open(output, 'w') as f:
        writer = csv.writer(f)
        r = ["N", "Count", "Percent of Total Queries", "Subsequence"]
        writer.writerow(r)
        for s in sorted(sequences, key=sequences.get, reverse=True):
            cnt = sequences[s]
            pct = "{0:.4f}".format(cnt/float(total))
            seq = " ".join([str(item) for item in s[1:]])
            r = [s[0], cnt, pct, seq]
            writer.writerow(r)

def lookup(dictionary, lookup_keys):
    return [dictionary[k] for k in lookup_keys]

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Prints list of longest common subsequences from all scheduled queries.")
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
    if not args.source:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    if args.output is None:
        args.output = "%s_fsm" % args.type
    if args.querytype is None:
        raise RuntimeError("You must specify a query type.")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    longest_common_subsequences(source, args.querytype, args.output)
