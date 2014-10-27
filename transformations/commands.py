from collections import defaultdict
import numpy
import matplotlib.pyplot as plt
from queryutils.arguments import get_arguments, lookup, SOURCES
from queryutils.parse import tokenize_query
from queryutils.splunktypes import lookup_categories, lookup_commands

def main(source, query_type, user_weighted, output):
    if user_weighted:
        return tally_weighted(source, query_type, output)
    else:
        return tally_unweighted(source, query_type, output)

def tally_weighted(source, query_type, output):

    stage_cnt = {}
    query_cnt = {}
    user_cnt = {}
    query_tfm_cnt = {}
    all_transforms = set()
    all_commands = defaultdict(set)

    for (user, query) in source.fetch_queries_by_user(query_type):

        transforms = lookup_categories(query)
        commands = lookup_commands(query)

        if not user in stage_cnt:
            stage_cnt[user] = defaultdict(int)
        if not user in query_cnt:
            query_cnt[user] = defaultdict(int)
        if not user in query_tfm_cnt:
            query_tfm_cnt[user] = defaultdict(int)

        for (t, c) in zip(transforms, commands):
            if not t in stage_cnt[user]:
                stage_cnt[user][t] = defaultdict(int)
            stage_cnt[user][t][c] += 1

        #for (t, c) in [(v,k) for (k,v) in dict(zip(commands, transforms)).iteritems()]:
        for (t, c) in set(zip(transforms, commands)):
            all_commands[t].add(c)
            if not t in query_cnt[user]:
                query_cnt[user][t] = defaultdict(int)
            query_cnt[user][t][c] += 1

        for t in set(transforms):
            query_tfm_cnt[user][t] += 1
            all_transforms.add(t)

    aggregate_stage_counts(stage_cnt, all_transforms, all_commands, output)
    aggregate_query_counts(query_cnt, query_tfm_cnt, all_transforms, all_commands, output)

def aggregate_stage_counts(stage_cnt, all_transforms, all_commands, output):
    out = "%s-weighted-stages-commands-counts.txt" % output
    stage_cnt_avg = {}
    stage_pct_avg = {}
    for (user, user_stage_cnt) in stage_cnt.iteritems():
        for transform in all_transforms:
            command_counts = user_stage_cnt.get(transform, None)
            if command_counts is not None:
                total_ntransform = float(sum(command_counts.values()))
            else:
                total_ntransform = 0.
            if not transform in stage_cnt_avg:
                stage_cnt_avg[transform] = defaultdict(list)
                stage_pct_avg[transform] = defaultdict(list)
            for command in all_commands[transform]:
                if command_counts is not None:
                    count = command_counts.get(command, 0.)
                    percent = float(count) / total_ntransform if total_ntransform > 0. else 0.
                    stage_cnt_avg[transform][command].append(count)
                    stage_pct_avg[transform][command].append(percent)
    for transform in all_transforms:
        for command in all_commands[transform]:
            stage_cnt_avg[transform][command] = numpy.mean(stage_cnt_avg[transform][command])
            stage_pct_avg[transform][command] = numpy.mean(stage_pct_avg[transform][command])

    with open(out, "w") as out:
        header = "%12s %50s %9s %5s\n" % ("transform", "command", "count", "percent")
        out.write(header)
        for (transform, command_counts) in stage_cnt_avg.iteritems():
            command_counts = sorted(command_counts.iteritems(), key=lambda x: x[1], reverse=True)
            for (command, count) in command_counts:
                percent = stage_pct_avg[transform][command]
                line = "%12s %50s %9d %3.2f\n" % (transform, command, count, percent)
                out.write(line)

def aggregate_query_counts(query_cnt, query_tfm_cnt, all_transforms, all_commands, output):
    out = "%s-weighted-queries-commands-counts.txt" % output
    query_cnt_avg = {}
    query_pct_avg = {}
    for (user, user_query_cnt) in query_cnt.iteritems():
        for transform in all_transforms:
            total_ntransform = query_tfm_cnt[user].get(transform, 0.)
            if not transform in query_cnt_avg:
                query_cnt_avg[transform] = defaultdict(list)
                query_pct_avg[transform] = defaultdict(list)
            command_counts = user_query_cnt.get(transform, None)
            for command in all_commands[transform]:
                if command_counts is not None:
                    count = command_counts.get(command, 0.)
                    percent = float(count) / total_ntransform if total_ntransform > 0. else 0.
                    query_cnt_avg[transform][command].append(count)
                    query_pct_avg[transform][command].append(percent)
    for transform in all_transforms:
        for command in all_commands[transform]:
            query_cnt_avg[transform][command] = numpy.mean(query_cnt_avg[transform][command])
            query_pct_avg[transform][command] = numpy.mean(query_pct_avg[transform][command])

    with open(out, "w") as out:
        header = "%12s %50s %9s %5s\n" % ("transform", "command", "count", "percent")
        out.write(header)
        for (transform, command_counts) in query_cnt_avg.iteritems():
            command_counts = sorted(command_counts.iteritems(), key=lambda x: x[1], reverse=True)
            for (command, count) in command_counts:
                percent = query_pct_avg[transform][command]
                line = "%12s %50s %9d %3.2f\n" % (transform, command, count, percent)
                out.write(line)

def tally_unweighted(source, query_type, output):

    stage_cnt = {}
    query_cnt = {}
    query_tfm_cnt = defaultdict(int)

    for query in source.fetch_queries(query_type):

        transforms = lookup_categories(query)
        commands = lookup_commands(query)

        for (t, c) in zip(transforms, commands):
            if not t in stage_cnt:
                stage_cnt[t] = defaultdict(int)
            stage_cnt[t][c] += 1

        for (t, c) in [(v,k) for (k,v) in dict(zip(commands, transforms)).iteritems()]:
            if not t in query_cnt:
                query_cnt[t] = defaultdict(int)
            query_cnt[t][c] += 1

        for t in set(transforms):
            query_tfm_cnt[t] += 1

    out = "%s-unweighted-stages-commands-counts.txt" % output
    with open(out, "w") as out:
        header = "%12s %50s %9s %5s\n" % ("transform", "command", "count", "percent")
        out.write(header)
        for (transform, command_counts) in stage_cnt.iteritems():
            total_transform = float(sum(command_counts.values()))
            command_counts = sorted(command_counts.iteritems(), key=lambda x:x[1], reverse=True)
            for (command, count) in command_counts:
                percent = float(count) / total_transform
                line = "%12s %50s %9d %8.2f\n" % (transform, command, count, percent)
                out.write(line)

    out = "%s-unweighted-queries-commands-counts.txt" % output
    with open(out, "w") as out:
        header = "%12s %50s %9s %5s\n" % ("transform", "command", "count", "percent")
        out.write(header)
        for (transform, command_counts) in query_cnt.iteritems():
            total_transform = query_tfm_cnt[transform]
            command_counts = sorted(command_counts.iteritems(), key=lambda x:x[1], reverse=True)
            for (command, count) in command_counts:
                percent = float(count) / total_transform
                line = "%12s %50s %9d %8.2f\n" % (transform, command, count, percent)
                out.write(line)


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
