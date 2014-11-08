from collections import defaultdict
import numpy
import matplotlib.pyplot as plt
from queryutils.arguments import get_arguments, lookup, SOURCES
from queryutils.query import QueryType
from queryutils.parse import tokenize_query, split_query_into_stages, parse_query
from queryutils.splunktypes import lookup_categories
from featurize import get_features, featurize_obj
import classify

def classify_stage(parsetree, features_code, classifier):
    feature_functions = get_features(features_code)
    features = featurize_obj(parsetree, feature_functions)
    if features is not None:
        features = features[1:] # first one is ID
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

FILTER_LABELS = {
    6: "Filters by regex",
    3: "Filters by index",
    2: "Filters by result of function",
    1: "Filters by specifying fields",
    10: "Filters by time range",
    8: "Filters by string contains",
    5: "Uses macro",
    0: "Deduplicates",
    4: "Filters by long logical condition",
    7: "Selects",
    9: "Uses subsearch",
}
AUGMENT_LABELS = {
    4: "Assigns simple value",
    3: "Date or time calculation",
    1: "Uses subsearch",
    7: "String manipulation",
    6: "Multi-value operation",
    2: "Conditional statement",
    0: "Arithmetic",
    5: "Assigns to group"
}
AGGREGATE_LABELS = {
    4: "Visualize aggregation over time",
    0: "Group by time",
    3: "Visualize aggregation",
    2: "Aggregate, sort, limit",
    1: "Aggregation"
}

TRANSFORM_LABELS = {
    "Filter": FILTER_LABELS,
    "Augment": AUGMENT_LABELS,
    "Aggregate": AGGREGATE_LABELS
}

def main(source, query_type, user_weighted, chosen_transform, examples, output, classify=False):
    if classify:
        classify_and_count(source, query_type, user_weighted, chosen_transform, examples, output)
    else:
        count_examples(examples, output, chosen_transform)

def count_examples(examples, output, transform):
    X, Y = classify.read_training_data(examples)
    counts = defaultdict(int)
    for y in Y:
        y = lookup_label(transform, y)
        counts[y] += 1
    print_counts(counts)
    plot_barchart(counts, output, transform)

def lookup_label(transform, code):
    return TRANSFORM_LABELS[transform][code]

def classify_and_count(source, query_type, user_weighted, chosen_transform, examples, output):
    clf = classify.fit_classifier(examples)
    if user_weighted:
        classify_and_count_weighted(source, query_type, chosen_transform, clf, output)
    else:
        classify_and_count_unweighted(source, query_type, chosen_transform, clf, output)

def classify_and_count_weighted(source, query_type, chosen_transform, clf, output):
    chosen_transform_counts = {}
    for (user, query) in source.fetch_queries_by_user(query_type):
        if not user in chosen_transform_counts:
            chosen_transform_counts[user] = defaultdict(int)
        classify_and_count_query(query, chosen_transform, chosen_transform_counts[user], clf)

def classify_and_count_unweighted(source, query_type, chosen_transform, clf, output):
    chosen_transform_counts = defaultdict(int)
    for query in fetch_queries(source, query_type):
        classify_and_count_query(query, chosen_transform, chosen_transform_counts, clf)
    print_counts(chosen_transform_counts, totalincl=True)
 
def print_counts(cnts, totalincl=False):
    for query in source.fetch_queries(query_type):
        count_classes_query(query, chosen_transform, chosen_transform_counts, clf)
    print_chosen_transform_counts(chosen_transform_counts)

def print_chosen_transform_counts(cnts):
    total = float(sum(cnts.values()))
    cnts = sorted(cnts.iteritems(), key=lambda x: x[1], reverse=True)
    for (label, cnt) in cnts:
        pct = cnt/total*100
        if totalincl:
            pct *= 2 # Because we count the total of transforms too
        print "%50s %6d %.2f" % (label, cnt, pct)

def classify_and_count_query(query, chosen_transform, counts, clf):
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

def plot_barchart(counts, output, transform):
    
    total = float(sum(counts.values()))
    counts = sorted(counts.iteritems(), key=lambda x: x[1], reverse=True)
    index = numpy.arange(len(counts))
    names = [k for (k,v) in counts]
    pcts = [v/total*100. for (k,v) in counts]
   
    plt.subplot()
    plt.bar(index, pcts, 1, color="c")
    plt.ylabel("% transformations", fontsize=18)
    plt.yticks(range(0, 100, 10), fontsize=12)
    plt.xticks(index + 0.5, names, rotation=-45, fontsize=16,
       rotation_mode="anchor", ha="left")
    plt.xlabel("Types of %s Transformations" % transform, fontsize=20)
    plt.tick_params(bottom="off")

    plt.autoscale(enable=True, axis="x", tight=None)
    plt.tight_layout()
    plt.savefig(output + ".pdf", dpi=400)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Bar graph describing how frequently each transformation appears in user queries.")
    parser.add_argument("-t", "--transform",
                        help="the transform to count")
    parser.add_argument("-e", "--examples",
                        help="the training data file to train the classifier (.csv)")
    parser.add_argument("-c", "--classify", action="store_true",
                        help="whether or not to classify the entire data set or simply count examples")
    args = get_arguments(parser, o=True, w=True)
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
    main(source, args.querytype, args.weighted, args.transform, args.examples, args.output, args.classify)

