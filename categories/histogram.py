from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
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

def main(source, output):
    category_counts, nqueries = tally_category_counts(source)
    create_histogram(category_counts, nqueries, output)

def tally_category_counts(source):
    category_counts = defaultdict(int)
    nqueries = 0
    for query in source.get_queries():
        categories = lookup_categories(query)
        if len(categories) > 0:
            nqueries += 1
            for category in categories:
                category_counts[category] += 1
    return category_counts, nqueries

def create_histogram(categories, total_queries, output):
    names = sorted(categories, key=categories.get, reverse=True)
    percents = convert_to_percents(categories)
    counts = sorted(categories.values(), reverse=True)
    ig = plt.figure(figsize=(13.5, 8.0))
    index = np.arange(len(categories))
    rects = plt.bar(index, counts, 1, color='c')
    plt.xlabel("Category", fontsize=20)
    plt.ylabel("Number of Commands", fontsize=20)
    plt.xticks(index + 0.5, names, rotation=-45, fontsize=20,
               rotation_mode="anchor", ha="left")
    plt.text(14, 252500, "N = " + str(total_queries) + " queries",
             fontsize=16, bbox=dict(facecolor='none', edgecolor='black', pad=10.0))
    plt.yticks(np.arange(0, 300001, 50000), fontsize=20)
    plt.tick_params(bottom='off')
    autolabel(rects, percents)
    plt.autoscale(enable=True, axis='x', tight=None)
    plt.tight_layout()
    plt.savefig(output + ".png", dpi=400)

def convert_to_percents(categories):
    percents = {}
    total = float(sum(categories.values()))
    for category in categories:
        count = float(categories[category])
        percents[category] = count / total * 100.
    percents = sorted(percents.values(), reverse=True)
    percents = ["{0:.0f}%".format(percent) for percent in percents]
    return percents

def autolabel(rects, counts):
    for ii, rect in enumerate(rects):
        height = rect.get_height()
        plt.text(
            rect.get_x() + rect.get_width() / 2., height +
            1000, '%s' % (counts[ii]),
            ha='center', va='bottom', fontsize=20)

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
    parser.add_argument("-o", "--output",
                        help="the name of the output file")
    args = parser.parse_args()
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if args.source is None:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    if args.output is None:
        args.output = "categories_histogram"
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(source, args.output)
