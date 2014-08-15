from collections import defaultdict
import numpy
import matplotlib.pyplot as plt
from queryutils.databases import PostgresDB, SQLite3DB
from queryutils.parse import tokenize_query, split_query_into_stages, parse_query
from queryutils.splunktypes import lookup_categories
from featurize import get_features, featurize_obj
import classify

SOURCES = {
    "postgresdb": (PostgresDB, ["database", "user", "password"]),
    "sqlite3db": (SQLite3DB, ["srcpath"])
}

def classify_stage(parsetree, features_code, classifier):
    feature_functions = get_features(features_code)
    features = featurize_obj(parsetree, feature_functions)
    if features is not None:
        feautures = features[1:] # first one is ID
    classification = classify.classify(features, classifier)
    return int(classification)

def classify_filter_stage(parsetree, clf):
    return classify_stage(parsetree, "filters01", clf)

def classify_augment_stage(parsetree, clf):
    return classify_stage(parsetree, "augments01", clf)

def classify_aggregate_stage(parsetree, clf):
    return classify_stage(parsetree, "aggregates01", clf)

CLASSIFY_STAGE = {
    "Filter": classify_filter_stage,
    "Augment": classify_augment_stage,
    "Aggregate": classify_aggregate_stage
}

class QueryType(object):
    INTERACTIVE = "interactive"
    SCHEDULED = "scheduled"

def main(source, query_type, user_weighted, chosen_transform, examples, output):
    count_classes(source, query_type, user_weighted, chosen_transform, examples, output)

def count_classes(source, query_type, user_weighted, chosen_transform, examples, output):
    clf = classify.fit_classifier(examples)
    if user_weighted:
        count_classes_weighted(source, query_type, chosen_transform, clf, output)
    else:
        count_classes_unweighted(source, query_type, chosen_transform, clf, output)

def count_classes_weighted(source, query_type, chosen_transform, clf, output):
    chosen_transform_counts = {}
    for (user, query) in fetch_queries_by_user(source, query_type):
        if not user in chosen_transform_counts:
            chosen_transform_counts[user] = defaultdict(int)
        count_classes_query(query, chosen_transform, chosen_transform_counts[user], clf)

def count_classes_unweighted(source, query_type, chosen_transform, clf, output):
    chosen_transform_counts = defaultdict(int)
    for query in fetch_queries(source, query_type):
        count_classes_query(query, chosen_transform, chosen_transform_counts, clf)
    print_chosen_transform_counts(chosen_transform_counts)
 
def print_chosen_transform_counts(cnts):
    total = float(sum(cnts.values()))
    cnts = sorted(cnts.iteritems(), key=lambda x: x[1], reverse=True)
    for (label, cnt) in cnts:
        pct = cnt/total*100*2 # Because we count the total of transforms too
        print "%20s %6d %.2f" % (label, cnt, pct)

def count_classes_query(query, chosen_transform, counts, clf):
    stages = split_query_into_stages(query)
    for pos, stage in enumerate(stages):
        transforms = lookup_categories(stage)
        if len(transforms) == 0:
            print query
            print stage
            continue
        if transforms[0] == chosen_transform:
            counts[chosen_transform] += 1
            p = parse_query(stage)
            if p is not None:
                p.position = pos
                code = CLASSIFY_STAGE[chosen_transform](p, clf)
                counts[code] += 1
            else:
                counts["UNPARSED"] += 1

def fetch_queries_by_user(source, query_type):
    source.connect()
    if query_type == QueryType.INTERACTIVE:
        ucursor = source.execute("SELECT id FROM users WHERE user_type is null")
    elif query_type == QueryType.SCHEDULED:
        ucursor = source.execute("SELECT id FROM users")
    else:
        raise RuntimeError("Invalid query type.")
    for row in ucursor.fetchall():
        user_id = row["id"]
        if query_type == QueryType.INTERACTIVE:
            sql = "SELECT text FROM queries WHERE is_interactive=true AND is_suspicious=false AND user_id=%s" % source.wildcard
        elif query_type == QueryType.SCHEDULED:
            sql = "SELECT DISTINCT text FROM queries WHERE is_interactive=false AND user_id=%s" % source.wildcard
        else:
            raise RuntimeError("Invalid query type.")
        qcursor = source.execute(sql, (user_id, )) 
        for row in qcursor.fetchall():
            query = row["text"]
            yield (user_id, query)
    source.close()

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

def plot_barchart(stage_percents, stages_label, query_percents, queries_label, output):
   
    spcts = sorted(stage_percents.iteritems(), key=lambda x: x[1], reverse=True)
    names = [k for (k,v) in spcts]
    qpcts = [query_percents[k]*100 for (k,v) in spcts]
    spcts = [v*100 for (k,v) in spcts]
    for (n, s, q) in zip(names, spcts, qpcts):
        print "%s, %.1f, %.1f" % (n, s, q)
    
    index = numpy.arange(len(stage_percents))

    plt.subplot(2, 1, 1)
    plt.bar(index, spcts, 1, color="r")
    plt.ylabel("% stages", fontsize=18)
    plt.yticks(range(0, 100, 10), fontsize=12)
    plt.xticks(index + 0.5, ["" for n in names])
    plt.text(10.5, 72, "N = %s" % stages_label,
        fontsize=16, bbox=dict(facecolor="none", edgecolor="black", pad=10.0))
    plt.tick_params(bottom="off")
    
    plt.subplot(2, 1, 2)
    plt.bar(index, qpcts, 1, color="c")
    plt.ylabel("% queries", fontsize=18)
    plt.yticks(range(0, 100, 10), fontsize=12)
    plt.xticks(index + 0.5, names, rotation=-45, fontsize=16,
       rotation_mode="anchor", ha="left")
    #plt.xlabel("Transformation Type", fontsize=20)
    plt.text(10, 80, "N = %s" % queries_label,
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
    parser.add_argument("-w", "--weighted", action="store_true",
                        help="if true, average across users")
    parser.add_argument("-t", "--transform",
                        help="the transform to count")
    parser.add_argument("-e", "--examples",
                        help="the training data file to train the classifier (.csv)")
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
    if args.examples is None:
        raise RuntimeError("You must provide training data.")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(source, args.querytype, args.weighted, args.transform, args.examples, args.output)

