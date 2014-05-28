
from argparse import ArgumentParser
import numpy as np
import matplotlib.pyplot as plt

import helpers.db as dbhelper
import helpers.commands as commhelper
import helpers.queries as qhelper

RESULTS_DIR = "results/"
TYPE = 'all'

total_queries = 0


def main(textlist):
    db = dbhelper.connect_db()
    querydata = dbhelper.get_data(db, TYPE)
    commands = commhelper.get_commands(textlist)
    categories, missing = process(querydata, commands)
    create_histogram(categories)
    write_missing(missing)


def process(querydata, commandslist):
    categories = {}
    missing = {}
    for query in querydata:
        if qhelper.validate_adhoc(query.lower()):
            commands, missing = split_into_commands(
                query.lower(), commandslist, missing)
            if commands != []:
                global total_queries
                total_queries += 1
                for command in commands:
                    if command not in categories:
                        categories[command] = 1
                    else:
                        categories[command] += 1
    return categories, missing


def split_into_commands(query, commands, missing):
    tokens = qhelper.tokenize(query)
    commands, missing = qhelper.split_into_commands(tokens, commands, TYPE,
                                                    missing_commands=missing, histogram=True)
    return commands, missing


def convert_to_percents(categories):
    percents = {}
    total = float(sum(categories.values()))
    for cat in categories:
        count = categories[cat]
        percents[cat] = count / total * 100
    percents = sorted(percents.values(), reverse=True)
    percents = ["{0:.0f}%".format(percent) for percent in percents]
    return percents


def create_histogram(categories):
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
    plt.savefig(RESULTS_DIR + "categories_histogram.png", dpi=400)


def autolabel(rects, counts):
    for ii, rect in enumerate(rects):
        height = rect.get_height()
        plt.text(
            rect.get_x() + rect.get_width() / 2., height +
            1000, '%s' % (counts[ii]),
            ha='center', va='bottom', fontsize=20)


def write_missing(missing):
    with open('results/nonlisted_commands.txt', 'w') as f:
        for command in sorted(missing, key=missing.get, reverse=True):
            f.write(command + ": " + str(missing[command]) + "\n")


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Creates heatmaps for bigrams of commands mapped onto their relational type.")
    parser.add_argument("commands", metavar="COMMANDS", type=str,
                        help="path to list of commands used (.txt)")
    args = parser.parse_args()
    main(args.commands)
