from collections import defaultdict
import numpy
import matplotlib.pyplot as plt
from queryutils.arguments import get_arguments, lookup, SOURCES
from queryutils.parse import tokenize_query
from queryutils.query import QueryType
from queryutils.splunktypes import lookup_categories

def main(source, query_type, transform):
    print_transform_data(source, query_type, transform)

def print_transform_data(source, query_type, transform):
    stats = defaultdict(int)
    ntransform_queries = ntransform_stages = 0
    users = set()
    for (user, query) in source.fetch_queries_by_user(query_type):
        transforms = lookup_categories(query)
        if transform in transforms:
            users.add(user)
            ntransform_queries += 1
            ntransform_stages += len([t for t in transforms if t == transform])
            stats[query] = transforms
            print "QUERY: %s" % query
            print "TRANSFORMS: [ %s ]" % " | ".join(transforms)
            print
    if len(stats) == 0:
        print "No queries with '%s's" % transform
    avg_transforms = numpy.mean([len([t for t in transforms if t == transform]) for (query, transforms) in stats.iteritems()])
    print "Number of total queries with %ss: %d" % (transform, ntransform_queries)
    print "Number of total stages with %ss: %d" % (transform, ntransform_stages)
    print "Number of distinct queries with %ss: %d" % (transform, len(stats.keys()))
    print "Average number of %s stages for such queries: %f" % (transform, avg_transforms)
    print "Number of users using %ss: %d" % (transform, len(users))

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Tallies queries, stages, and users containing a given transformation.")
    parser.add_argument("-t", "--transform",
                        help="the type of transformation to examine")
    args = get_arguments(parser)
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if args.source is None:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    if args.querytype is None:
        raise RuntimeError("You must specify a query type.")
    if args.transformation is None:
        raise RuntimeError("You must specify a transformation type.")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    main(source, args.querytype, args.transform)
