
from argparse import ArgumentParser
import matplotlib.pyplot as plt
from pylab import *

import helpers.db as dbhelper
import helpers.commands as commhelper
import helpers.queries as qhelper

RESULTS_DIR = "results/fix_adhoc/longest_common_subsequences/"
RANGE = [2,3,4,5,6]
QUERY_TYPES = ['unique_adhoc', 'unique_scheduled']

sequences = {}


def main(textlist):
    db = dbhelper.connect_db()
    commands = commhelper.get_commands(textlist)
    for type in QUERY_TYPES:
        run(db, commands, type)


def run(db, commands, type):
    total_sequences = {}
    users = set(dbhelper.get_users(db, type))
    total = dbhelper.get_total_len(db,type)
    for user in users:
        print "Getting data for user " + str(user) + "..."
        querydata = dbhelper.get_data_for_user(user, db, type)
        for N in RANGE:
            total_sequences = preprocess(querydata, total_sequences, N, commands)

    total_sequences = {k: v / float(len(users)) for k, v in total_sequences.items()}
    write_lcs(total_sequences, type, total)


def preprocess(querydata, gramtab, N, commandslist):
    for query in querydata:
        if qhelper.validate_adhoc(query):
            commands = split_into_commands(query, commandslist)
            if commands != []:
                for i, command in enumerate(commands[:-N+1]):
                    sequence = str(N)+(' ').join(commands[i:i+N])
                    if sequence not in gramtab:
                        gramtab[sequence] = 0
                    gramtab[sequence] += 1
    return gramtab


def split_into_commands(query, commands):
    tokens = qhelper.tokenize(query)
    commands = qhelper.split_into_commands(tokens, commands, '')
    return commands


def write_lcs(gramtab, type, total):
    with open(RESULTS_DIR + type + ".txt", 'w') as f:
        f.write((", ").join(['N','Count','Percent of Total Queries','Subsequence'])+'\n')
        for seq in sorted(gramtab, key=gramtab.get, reverse=True):
            f.write((", ").join([seq[0],
                str(gramtab[seq]),
                "{0:.4f}".format(gramtab[seq]/float(total)),
                seq[1:]]) + '\n')
        f.write('\n')

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Prints list of top sequences of categories in a query.")
    parser.add_argument("commands", metavar="COMMANDS", type=str,
                        help="path to list of commands used (.txt)")
    args = parser.parse_args()
    main(args.commands)
