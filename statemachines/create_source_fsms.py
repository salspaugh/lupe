
from argparse import ArgumentParser
import re

import scripts.categories_scripts.create_fsm as fsm
import scripts.categories_scripts.create_categories_heatmaps as cat
import helpers.db as dbhelper
import helpers.commands as commhelper
import helpers.queries as qhelper


N = float(203691)
THRESHOLD = 0.0
START_TOKEN = '<start>'
END_TOKEN = '<end>'
QUERY_TYPES = ['unique_scheduled']
SOURCE_TYPES = ['vmware:perf:','solaris3-web-access']
FREQS_DIR = 'results/fix_adhoc/relations_bigram_heatmaps/sourcetypes/'
RESULTS_DIR = 'results/fix_adhoc/fsm_graphs/sourcetypes/'


def main(textlist):
    commands = commhelper.get_commands(textlist)
    for type in QUERY_TYPES:
        run_analysis(commands, type)
                


def run_analysis(commands, type):
    db = dbhelper.connect_db()
    for source in SOURCE_TYPES:
        total_gramtab = {}
        users = set(dbhelper.get_users(db, type))
        total = 0
        total_users = 0
        for user in users:
            print "Getting data for user " + str(user) + "..."
            querydata = dbhelper.get_data_for_user(user, db, type)
            querydata = get_queries_of_source(source, querydata)
            total += len(querydata)
            gramtab = preprocess(querydata, commands, type)
            if gramtab != {}:
                total_users += 1
                for first in gramtab:
                    for second in gramtab[first]:
                        edge = first + " " + second
                        if edge not in total_gramtab:
                            total_gramtab[edge] = 0
                        total_gramtab[edge] += cat.lookup(first, second, gramtab)
        if total_gramtab != {}:
            total_gramtab = {k: v / float(total_users) for k, v in total_gramtab.items()}
            write_frequencies(total_gramtab, type, source, total)
            fsm.create_fsm(source + "_" + type, parse_dir=FREQS_DIR, \
            results_dir=RESULTS_DIR, threshold=THRESHOLD)

def get_queries_of_source(source, querydata):
    retdata = []
    st = re.compile(".*\s*(sourcetype)\s*(=)\s*['\"]?("+source+").*['\"]?")
    s = re.compile(".*\s*(source)\s*(=)\s*['\"]?("+source+").*['\"]?")
    for query in querydata:
        if st.match(query) or s.match(query):
            retdata.append(query)
    return retdata

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


def write_frequencies(gramtab, type, source, count):
    with open(FREQS_DIR + source + "_" + type + ".txt", 'w') as f:
        f.write(str(count) + '\n')
        for edge in sorted(gramtab, key=gramtab.get, reverse = True):
            f.write(edge + " : " + str(gramtab[edge]) + "\n")

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Creates heatmaps for bigrams of commands mapped onto their relational type.")
    parser.add_argument("commands", metavar="COMMANDS", type=str,
                        help="path to list of commands used (.txt)")
    args = parser.parse_args()
    main(args.commands)
