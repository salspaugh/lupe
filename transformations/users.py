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
    tally_users_per(source, query_type, output, Category.TRANSFORMS)
    tally_users_per(source, query_type, output, Category.COMMANDS)

def tally_users_per(source, query_type, output, category):

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
        args.output = "categories_histogram"
    if args.querytype is None:
        raise RuntimeError("You must specify a query type.")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(source, args.querytype, args.output)
