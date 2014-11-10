from collections import defaultdict
import numpy
import matplotlib.pyplot as plt
from queryutils.arguments import get_arguments, lookup, SOURCES
from queryutils.parse import tokenize_query
from queryutils.query import QueryType
from queryutils.splunktypes import lookup_categories, lookup_commands

class Category(object):
    TRANSFORMS = "transforms"
    COMMANDS = "commands"

def main(source, query_type, output):
    """Calls tally_users_per() on transformations and commands and prints average, max, and min counts
    of each transformation or command per user.

    This main function first calls tally_users_per() on transformations to calculate and print the
    average distinct transformations, max distinct transformations, min distinct transformations
    and average total transformations per user. It then calls tally_users_per() again and does the
    same for commands.

    :param source: where to fetch the data and arguments
    :type source: either a CSVFiles, JSONFiles, PostgresDB, or SQLite3DB
    :param query_type: type of queries to look at; either scheduled or interactive
    :type query_type: str
    :param output: the name of the output file containing the barchart
    :type output: str
    """
    tally_users_per(source, query_type, output, Category.TRANSFORMS)
    tally_users_per(source, query_type, output, Category.COMMANDS)

def tally_users_per(source, query_type, output, category):
    """Calculates and prints average, max, and min counts of each transformation or command per user.

    This function calculates and prints the average distinct transformations, max distinct transformations,
    min distinct transformations and average total transformations per user.

    :param source: where to fetch the data and arguments
    :type source: either a CSVFiles, JSONFiles, PostgresDB, or SQLite3DB
    :param query_type: type of queries to look at; either scheduled or interactive
    :type query_type: str
    :param output: the name of the output file containing the barchart
    :type output: str
    :param category: the category to tally, either transformations or commands
    :type category: Category
    """
    if category == Category.TRANSFORMS:
        lookup_query = lookup_categories
    elif category == Category.COMMANDS:
        lookup_query = lookup_commands

    user_cnt = defaultdict(set)
    ctgy_cnt = defaultdict(list)

    for (user, query) in source.fetch_queries_by_user(query_type):
        categories = lookup_query(query)
        for c in categories:
            user_cnt[c].add(user)
            ctgy_cnt[user].append(c)

    out = "%s-distinct-users-per-%s.txt" % (output, category)
    with open(out, "w") as out:
        header = "%12s %6s\n" % (category, "nusers")
        out.write(header)
        for (c, users) in user_cnt.iteritems():
            line = "%12s %6d\n" % (c, len(users))
            out.write(line)
    distinct_ctgy_per = [len(set(c)) for c in ctgy_cnt.values()]
    print "Average distinct %s per user: %.4f:" %  (category, numpy.mean(distinct_ctgy_per))
    print "Max distinct %s per user: %.4f:" %  (category, numpy.max(distinct_ctgy_per))
    print "Min distinct %s per user: %.4f:" %  (category, numpy.min(distinct_ctgy_per))
    print "Average total %s per user: %.4f:" % (category, numpy.mean([len(c) for c in ctgy_cnt.values()]))

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Tallies and prints average distinct, max distinct, min distinct, and average total \
                    transforms and commands per user.")
    args = get_arguments(parser, o=True)
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if args.source is None:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    if args.output is None:
        args.output = "user_tallies"
    if args.querytype is None:
        raise RuntimeError("You must specify a query type.")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(source, args.querytype, args.output)
