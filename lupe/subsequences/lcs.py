from collections import defaultdict
from queryutils.arguments import get_arguments, lookup, SOURCES
from queryutils.query import QueryType
from queryutils.splunktypes import lookup_categories
import csv

MIN_LEN = 2
MAX_LEN = 6

def longest_common_subsequences(source, querytype, output):
    nusers = nqueries = 0.
    sequences = defaultdict(int)
    for user in source.get_users_with_queries():
        if querytype == QueryType.INTERACTIVE:
            queries = [q for q in user.interactive_queries
                if not q.is_suspicious]
        elif querytype == QueryType.SCHEDULED:
            queries = set([q.text for q in user.noninteractive_queries])
        else:
            raise runtimeerror("invalid query type.")
        nqueries += len(queries)
        for query in queries: # TODO: Filter out bad queries?
            categories = lookup_categories(query)
            for length in range(MIN_LEN, MAX_LEN+1):
                for idx, item in enumerate(categories[:-length+1]):
                    sequence = tuple([length] + categories[idx:idx+length])
                    sequences[sequence] += 1.
        nusers += 1.
    sequences = { k: v / nusers for k, v in sequences.items()}
    write_sequences(sequences, output, nqueries)

def write_sequences(sequences, output, total):
    with open(output, 'w') as f:
        writer = csv.writer(f)
        r = ["N", "Count", "Percent of Total Queries", "Subsequence"]
        writer.writerow(r)
        for s in sorted(sequences, key=sequences.get, reverse=True):
            cnt = sequences[s]
            pct = "{0:.4f}".format(cnt/float(total))
            seq = " ".join([str(item) for item in s[1:]])
            r = [s[0], cnt, pct, seq]
            writer.writerow(r)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Prints list of longest common subsequences from all scheduled queries.")
    args = get_arguments(parser, o=True)
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    if not args.source:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    if args.output is None:
        args.output = "%s_fsm" % args.type
    if args.querytype is None:
        raise RuntimeError("You must specify a query type.")
    src_class = SOURCES[args.source][0]
    src_args = lookup(vars(args), SOURCES[args.source][1])
    source = src_class(*src_args)
    longest_common_subsequences(source, args.querytype, args.output)
