from queryutils.databases import PostgresDB, SQLite3DB
from queryutils.parse import tokenize_query, split_query_into_stages, parse_query
from queryutils.splunktypes import lookup_categories
from featurize import get_features, featurize_obj
import json
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


def main(source, query_type, transform, output, append, verify):
    if verify:
        verify(transform, output)
    else:
        sort(source, query_type, transform, output, append)

def verify(transform, output):
    status_filename = "%s-verification-results.json" % output
    results = {
        "failed": {},
        "succeeded": {},
        }
    verified_filename = "%s-verified-examples.csv" % output
    with open(status_filename, "w") as status, open(verified_filename, "w") as verified:
        status_writer = csv.writer(status)
        example_writer = csv.writer(verified)
        records = read_verification_records(output)
        has_header = False
        for (identifier, record) in records.iteritems():
            parsetree = record["parsetree"]
            old_code = record["code"]
            new_code = present_for_sorting(parsetree, SORTING_CODES[transform])
            if old_code == new_code:
                features = lookup_features(parsetree, FEATURE_CODES[transform])
                features = [float(f) for f in features[1:]]
                if not has_header:
                    write_header(features, example_writer)
                    has_header = True
                example_writer.writerow([code] + features)
                results["succeeded"][identifier] = record
            else:
                record["diff"] = new_code
                results["failed"][identifier] = record
        print "Verified: %d results, %d failed" % (len(results), len(results["failed"]))
        json.dump(results, status)

def sort(source, query_type, transform, output, append):
    records = {}
    records["coverage"] = set()
    examples_per_category = defaultdict(int)
    if append:
        records = read_verification_records(output)
        examples_per_category = tally_examples_per_category(records)
    print records.keys()
    examples_filename = "%s-sorted-examples.csv" % output
    write_bit = "a" if append else "w"
    with open(examples_filename, write_bit) as examples:
        writer = csv.writer(examples)
        has_header = False
        for query in fetch_queries(source, query_type):
            for parsetree in parsed_stages(query, transform):
                identifier = "%d.%d" % (len(records), parsetree.position)
                if identifier in records: continue
                features = lookup_features(parsetree, FEATURE_CODES[transform])
                if features is None: continue
                features = [float(f) for f in features[1:]]
                if tuple(features) in records["coverage"]: continue
                records["coverage"].add(tuple(features))
                if not has_header:
                    write_header(features, writer)
                    has_header = True
                code = present_for_sorting(identifier, parsetree, SORTING_CODES[transform])
                if code == "EXIT":
                    finish_sorting(records, output)
                    return
                if valid_code(code, SORTING_CODES[transform]):
                    examples_per_category[code] += 1
                    writer.writerow([code] + features)
                    print "\tWrote a row!"
                insert_record(identifier, parsetree, code, records)
                if wrote_enough_examples(examples_per_category, records):
                    finish_sorting(records, output)
                    return
    finish_sorting(records, output)

def insert_record(identifier, parsetree, code, records):
    record = {
        "parsetree": parsetree._str_tree(),
        "identifier": identifier,
        "code": code
    }
    records[identifier] = record

def wrote_enough_examples(counts, records):
    return all([v > 10 for v in counts.values()]) or len(records) > 300

def finish_sorting(records, output):
    print "\tEXITING NOW!"
    write_verification_records(records, output)

def valid_code(code, valid_codes):
    return code in valid_codes.values() and code != valid_codes["unknown"]

def write_header(x, writer):
    header = ["X%d"]*len(x) 
    header = [s % i for i, s in enumerate(header)]
    header = ["Y"] + header
    writer.writerow(header)

def read_verification_records(output):
    records_filename = "%s-verification.json" % output
    with open(records_filename) as record:
        return json.load(record)

def write_verification_records(data_to_verify, output):
    c = data_to_verify["coverage"]
    data_to_verify["coverage"] = list(c)
    records_filename = "%s-verification.json" % output
    with open(records_filename, "w") as record:
        json.dump(data_to_verify, record)

def tally_examples_per_category(records):
    counts = defaultdict(int)
    for (identifier, record) in records.iteritems():
        counts[record["code"]] += 1
    return counts

def present_for_sorting(identifier, parsetree, sorting_codes):
    msg = make_message(identifier, parsetree, sorting_codes)
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

def make_message(identifier, parsetree, sorting_codes):
    msg = "\n\n-------------------------------------------------------------\n"
    msg += "Classify item %s: \n %s\nOptions are:\n" % (identifier, parsetree._str_tree())
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
    parser.add_argument("-n", "--append", action="store_true",
                        help="whether or not to append to the data named by output")
    parser.add_argument("-y", "--verify", action="store_true",
                        help="whether or not to verify the data named by output")
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
    main(source, args.querytype, args.transform, args.output, args.append, args.verify)
