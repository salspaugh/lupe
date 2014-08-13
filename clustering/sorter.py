from queryutils.databases import PostgresDB, SQLite3DB
from queryutils.parse import tokenize_query, split_query_into_stages, parse_query
from queryutils.splunktypes import lookup_categories
from featurize import get_features, featurize_obj
import csv
from collections import defaultdict

SOURCES = {
    "postgresdb": (PostgresDB, ["database", "user", "password"]),
    "sqlite3db": (SQLite3DB, ["srcpath"])
}

class QueryType(object):
    INTERACTIVE = "interactive"
    SCHEDULED = "scheduled"

FEATURE_CODES = {
    "Filter": "filters01",
    "Augment": "augments01",
    "Aggregate": "aggregates01" 
}

FILTER_CODES = {
    "regex": 6,
    "index": 3,
    "function_based": 2,
    "field_value_search": 1,
    "time_range_search": 10,
    "simple_string_search": 8,
    "macro": 5,
    "dedup": 0,
    "logical": 4,
    "selection": 7,
    "subsearches": 9,
    "unknown": -1
    }
AUGMENT_CODES = {
    "field_value_assignments": 4,
    "datetime_conversion": 3,
    "complicated": 1,
    "string_manipulation": 7,
    "multivalue": 6,
    "conditionals": 2,
    "arithmetic": 0,
    "grouping": 5,
    "unknown": -1
    }
AGGREGATE_CODES = {
    "visualize_time": 4,
    "by_time": 0,
    "visualize": 3,
    "top": 2,
    "standard": 1,
    "unknown": -1
    }
SORTING_CODES = {
    "Filter": FILTER_CODES,
    "Augment": AUGMENT_CODES,
    "Aggregate": AGGREGATE_CODES 
}


def main(source, query_type, transform, output, verify):
    if verify:
        verify()
    else:
        sort(source, query_type, transform, output)

def verify():
    pass

def sort(source, query_type, transform, output):
    seen = set()
    verification = []
    counts = defaultdict(int)
    total = 0
    examples_filename = "%s-sorted-examples.csv" % output
    with open(examples_filename, "w") as examples:
        writer = csv.writer(examples)
        has_header = False
        for query in fetch_queries(source, query_type):
            for parsetree in parsed_stages(query, transform):
                identifier = "%d.%d" % (total, parsetree.position)
                if identifier in seen:
                    continue
                seen.add(identifier)
                code = process_parsetree(parsetree, transform, writer):
                if code == "EXIT":
                    write_verification(verification, output)
                    return
                record = {
                    "parsetree": parsetree._str_tree(),
                    "identifier": identifier,
                    "code": code
                }
                verification.append(record)

def write_verification(data_to_verify, output):
    records_filename = "%s-verification.json" % output
    with open(records_filename) as record:
        json.dump(data_to_verify, record)

def process_parsetree(parsetree, transform, writer)
    features = lookup_features(parsetree, FEATURE_CODES[transform])
    if features is not None:
        x = [float(f) for f in features[1:]]
        if not has_header:
            header = ["X%d"]*len(x) 
            header = [s % i for i, s in enumerate(header)]
            header = ["Y"] + header
            writer.writerow(header)
            has_header = True
        code = present_for_sorting(parsetree, SORTING_CODES[transform])
        if code == "EXIT":
            print "\tEXITING NOW!"
            return "EXIT"
        if code in SORTING_CODES[transform].values() and code != SORTING_CODES[transform]["unknown"]:
            counts[code] += 1
            total += 1
            y = [code]
            writer.writerow(y + x)
            print "\tWrote a row!"
            if all([v > 10 for v in counts.values()]) or total > 300:
                print "ALL DONE!"
                return "EXIT"

def present_for_sorting(parsetree, sorting_codes):
    msg = make_message(parsetree, sorting_codes)
    reverse_codes = { v:k for (k,v) in sorting_codes.iteritems() }
    while True:
        input = raw_input(msg)
        if input == "X":
            return "EXIT"
        try:
            input = int(input)
        except:
            pass
        if input in sorting_codes.values():
            check = "\tYou entered: '%s' -- is that correct? (y/n)  " % reverse_codes[input]
            answer = raw_input(check)
            if answer == "y":
                return input
        else:
            print "Sorry. Unrecognized code. Try again."
    return input

def make_message(parsetree, sorting_codes):
    msg = "\n\n-------------------------------------------------------------\n"
    msg += "Classify:\n %s\nOptions are:\n" % parsetree._str_tree() 
    codes = sorted(sorting_codes.iteritems(), key=lambda x: x[1])
    for (name, code) in codes:
        msg = "%s\n\t\t%d (%s)" % (msg, code, name)
    msg += "\n\n\tEnter X to exit. Input: "
    return msg

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

def parsed_stages(query, chosen_transform):
    stages = split_query_into_stages(query)
    for pos, stage in enumerate(stages):
        transforms = lookup_categories(stage)
        if len(transforms) == 0:
            print query
            print stage
            continue
        if transforms[0] == chosen_transform:
            p = parse_query(stage)
            if p is not None:
                p.position = pos
                yield p

def lookup_features(parsetree, features_code):
    feature_functions = get_features(features_code)
    features = featurize_obj(parsetree, feature_functions)
    return features


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
    parser.add_argument("-t", "--transform",
                        help="the transform to count")
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
    main(source, args.querytype, args.transform, args.output)
