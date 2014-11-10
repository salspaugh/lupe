from collections import defaultdict
import numpy
import matplotlib.pyplot as plt
from queryutils.arguments import get_arguments, lookup, SOURCES
from queryutils.parse import tokenize_query
from queryutils.splunktypes import lookup_categories

def main(source, query_type, user_weighted, output):
    """Tallies and creates bar chart for percentage of stages and percentage of
    queries for each type of transformation.

    This main function calls tally() to calculate the percentage of stages
    and percentage of queries for each type of transformation. Then it calls
    plot_barchart() to create a bar chart figure of the percentage of stages
    and percentage of queries.

    :param source: where to fetch the data and arguments
    :type source: either a CSVFiles, JSONFiles, PostgresDB, or SQLite3DB
    :param query_type: type of queries to look at; either scheduled or interactive
    :type query_type: str
    :param user_weighted: true if the data should be averaged across users
    :type user_weighted: boolean
    :param output: the name of the output file containing the barchart
    :type output: str
    """
    stage_pcts, nstages, query_pcts, nqueries = tally(source, query_type, user_weighted)
    label = "weighted" if user_weighted else "unweighted"
    output = "%s-%s" % (output, label)
    stages_textbox = "%.1f stages per user" if user_weighted else "%d stages"
    queries_textbox = "%.1f queries per user" if user_weighted else "%d queries"
    stages_textbox = stages_textbox % nstages
    queries_textbox = queries_textbox % nqueries
    plot_barchart(stage_pcts, stages_textbox, query_pcts, queries_textbox, output)

def tally(source, query_type, user_weighted):
    """Calls either tally_weighted() or tally_unweighted() to tally percentage of stages
    and percentage of queries for each type of transformation.

    :param source: where to fetch the data and arguments
    :type source: either a CSVFiles, JSONFiles, PostgresDB, or SQLite3DB
    :param query_type: type of queries to look at; either scheduled or interactive
    :type query_type: str
    :param user_weighted: true if the data should be averaged across users
    :type user_weighted: boolean
    :rtype: dict, int, dict, int
    """
    if user_weighted:
        return tally_weighted(source, query_type)
    else:
        return tally_unweighted(source, query_type)

def tally_weighted(source, query_type):
    """Tallies percentage of stages and percentage of queries for each type of
    transformation averaged across users.

    :param source: where to fetch the data and arguments
    :type source: either a CSVFiles, JSONFiles, PostgresDB, or SQLite3DB
    :param query_type: type of queries to look at; either scheduled or interactive
    :type query_type: str
    :rtype: dict, int, dict, int
    """
    stage_cnt = {}
    nstages = 0
    nstages_per_user = defaultdict(int)

    query_cnt = {}
    nqueries = 0
    nqueries_per_user = defaultdict(int)
    all_transforms = set()

    for (user, query) in source.fetch_queries_by_user(query_type):

        transforms = lookup_categories(query)

        nstages += len(transforms)
        nstages_per_user[user] += len(transforms)
        nqueries += 1
        nqueries_per_user[user] += 1

        if not user in stage_cnt:
            stage_cnt[user] = defaultdict(int)
        if not user in query_cnt:
            query_cnt[user] = defaultdict(int)

        for t in transforms:
            stage_cnt[user][t] += 1
        for t in set(transforms):
            all_transforms.add(t)
            query_cnt[user][t] += 1

    stage_pct = defaultdict(list)
    for (user, transform_counts) in stage_cnt.iteritems():
        user_nstages = float(sum(transform_counts.values()))
        assert user_nstages == nstages_per_user[user]
        for t in all_transforms:
            count = transform_counts.get(t, 0.)
            user_pct = count / user_nstages
            stage_pct[t].append(user_pct)
    stage_pct = { t: numpy.mean(pcts) for (t, pcts) in stage_pct.iteritems() }

    query_pct = defaultdict(list)
    for (user, transform_counts) in query_cnt.iteritems():
        user_nquerys = float(nqueries_per_user[user])
        for t in all_transforms:
            count = transform_counts.get(t, 0.)
            user_pct = count / user_nquerys
            query_pct[t].append(user_pct)
    query_pct = { t: numpy.mean(pcts) for (t, pcts) in query_pct.iteritems() }

    nstages_per_user = numpy.mean(nstages_per_user.values())
    nqueries_per_user = numpy.mean(nqueries_per_user.values())
    return stage_pct, nstages_per_user, query_pct, nqueries_per_user

def tally_unweighted(source, query_type):
    """Tallies percentage of stages and percentage of queries for each type of
    transformation.

    :param source: where to fetch the data and arguments
    :type source: either a CSVFiles, JSONFiles, PostgresDB, or SQLite3DB
    :param query_type: type of queries to look at; either scheduled or interactive
    :type query_type: str
    :rtype: dict, int, dict, int
    """
    stage_cnt = defaultdict(int)
    nstages = 0

    query_cnt = defaultdict(int)
    nqueries = 0

    for query in source.fetch_queries(query_type):

        transforms = lookup_categories(query)

        nstages += len(transforms)
        nqueries += 1

        for t in transforms:
            stage_cnt[t] += 1
        for t in set(transforms):
            query_cnt[t] += 1

    stage_pct = { t: float(cnt)/nstages for (t, cnt) in stage_cnt.iteritems() }
    query_pct = { t: float(cnt)/nqueries for (t, cnt) in query_cnt.iteritems() }

    return stage_pct, nstages, query_pct, nqueries

def plot_barchart(stage_percents, stages_label, query_percents, queries_label, output):
    """Plots bar chart of percentage of stages and percentage of queries for each type of transformation.

    :param stage_percents: percentage of stages per transformation
    :type stage_percents: dict
    :param stages_label: string labeling textbox of total number of stages
    :type stages_label: str
    :param query_percents: percentage of queries per transformation
    :type query_percents: dict
    :param queries_label: string labeling textbox of total number of queries
    :type queries_label: str
    :param output: the name of the output file containing the barchart
    :type output: str
    """

    spcts = sorted(stage_percents.iteritems(), key=lambda x: x[1], reverse=True)
    names = [k for (k,v) in spcts]
    qpcts = [query_percents[k]*100 for (k,v) in spcts]
    spcts = [v*100 for (k,v) in spcts]
    for (n, s, q) in zip(names, spcts, qpcts):
        print "%s, %.1f, %.1f" % (n, s, q)

    index = numpy.arange(len(stage_percents))

    plt.subplot(2, 1, 1)
    rects = plt.bar(index, spcts, 1, color="r")
    autolabel(rects, spcts)
    plt.ylabel("% stages", fontsize=18)
    plt.yticks(range(0, 100, 10), fontsize=12)
    plt.xticks(index + 0.5, ["" for n in names])
    plt.text(10.5, 72, "N = %s" % stages_label,
        fontsize=16, bbox=dict(facecolor="none", edgecolor="black", pad=10.0))
    plt.tick_params(bottom="off")

    plt.subplot(2, 1, 2)
    rects = plt.bar(index, qpcts, 1, color="c")
    autolabel(rects, qpcts)
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

def autolabel(rects, counts):
    for ii, rect in enumerate(rects):
        height = rect.get_height()
        plt.text(
            rect.get_x() + rect.get_width() / 2., height +
            1000, "%.2f" % (counts[ii]),
            ha="center", va="bottom", fontsize=20)

def lookup(dictionary, lookup_keys):
    return [dictionary[k] for k in lookup_keys]

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Bar graph describing how frequently each transformation appears in user queries.")
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
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(source, args.querytype, args.weighted, args.output)
