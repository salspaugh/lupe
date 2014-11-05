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
    for (user, query) in source.fetch_queries_by_user(query_type):
        if not user in chosen_transform_counts:
            chosen_transform_counts[user] = defaultdict(int)
        count_classes_query(query, chosen_transform, chosen_transform_counts[user], clf)

def count_classes_unweighted(source, query_type, chosen_transform, clf, output):
    chosen_transform_counts = defaultdict(int)
    for query in source.fetch_queries(query_type):
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

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Bar graph describing how frequently each transformation appears in user queries.")
    parser.add_argument("-t", "--transform",
                        help="the transform to count")
    parser.add_argument("-e", "--examples",
                        help="the training data file to train the classifier (.csv)")
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
    main(source, args.querytype, args.weighted, args.transform, args.examples, args.output)

