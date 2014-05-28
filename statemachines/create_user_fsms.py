
from argparse import ArgumentParser

import scripts.categories_scripts.create_fsm as fsm
import scripts.categories_scripts.create_categories_heatmaps as cat
import helpers.db as dbhelper
import helpers.commands as commhelper
import helpers.queries as qhelper


N = 203691 # all queries
RUN = 1
QUERY_TYPES = ['unique_scheduled']
FREQS_DIR = 'results/fix_adhoc/relations_bigram_heatmaps/user_weighted/'
RESULTS_DIR = 'results/fix_adhoc/fsm_graphs/user_weighted/'


def main(textlist):
    commands = commhelper.get_commands(textlist)
    for type in QUERY_TYPES:
        if RUN:
            run_analysis(commands, type)
        fsm.create_fsm(type, parse_dir=FREQS_DIR, \
            results_dir=RESULTS_DIR)


def run_analysis(commands, type):
    db = dbhelper.connect_db()
    total_gramtab = {}
    users = set(dbhelper.get_users(db, type))
    total = float(dbhelper.get_total_len(db, type))
    for user in users:
        print "Getting data for user " + str(user) + "..."
        querydata = dbhelper.get_data_for_user(user, db, type)
        gramtab = preprocess(querydata, commands, type)
        for first in gramtab:
            for second in gramtab[first]:
                edge = first + " " + second
                print "Adding edge to tab: " + edge
                if edge not in total_gramtab:
                    total_gramtab[edge] = 0
                total_gramtab[edge] += cat.lookup(first, second, gramtab)
        print "Next user...\n"
    total_gramtab = {k: v / len(users) for k, v in total_gramtab.items()}
    write_frequencies(total_gramtab, type, total/N)


def preprocess(queries, commands, type):
    gramtab = {}
    for query in queries:
        if qhelper.validate_adhoc(query):
            gramtab = tally_completions(query, gramtab, commands, type)
    return gramtab


def tally_completions(query, gramtab, commandslist, type):
    commands = split_into_commands(
        query, commandslist, type)
    gramtab,c = qhelper.tally_completions(commands, gramtab,0)
    return gramtab


def split_into_commands(query, commands, type):
    tokens = qhelper.tokenize(query)
    commands = qhelper.split_into_commands(tokens, commands, type)
    return commands


def write_frequencies(gramtab, type, frac):
    with open(FREQS_DIR + type + ".txt", 'w') as f:
        f.write(str(frac) + '\n')
        for edge in sorted(gramtab, key=gramtab.get, reverse = True):
            f.write(edge + " : " + str(gramtab[edge]) + "\n")


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Creates heatmaps for bigrams of commands mapped onto their relational type.")
    parser.add_argument("commands", metavar="COMMANDS", type=str,
                        help="path to list of commands used (.txt)")
    args = parser.parse_args()
    main(args.commands)
