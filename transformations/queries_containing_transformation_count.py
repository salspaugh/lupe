from collections import defaultdict
from queryutils.databases import PostgresDB, SQLite3DB
from queryutils.files import CSVFiles, JSONFiles
from queryutils.parse import tokenize_query
from queryutils.splunktypes import lookup_categories

SOURCES = {
    "csvfiles": (CSVFiles, ["path", "version"]),
    "jsonfiles": (JSONFiles, ["path", "version"]),
    "postgresdb": (PostgresDB, ["database", "user", "password"]),
    "sqlite3db": (SQLite3DB, ["srcpath"])
}

def main(source):
    category_counts, nqueries = tally_category_counts(source)
    print "Total Queries:", nqueries
    category_counts = sorted(category_counts.iteritems(), key=lambda x: x[1])
    print "Transformation, Number, Percent"
    for (category, count) in category_counts:
        print "%s, %d, %f" % (category, count, float(count) / float(nqueries))

def tally_category_counts(source):
    category_counts = defaultdict(int)
    nqueries = 0
    for query in source.get_queries():
        categories = set(lookup_categories(query))
        if len(categories) > 0:
            nqueries += 1
            for category in categories:
                category_counts[category] += 1
    return category_counts, nqueries

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
    args = parser.parse_args()
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if args.source is None:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(source)
