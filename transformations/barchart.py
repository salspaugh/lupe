from collections import defaultdict
import numpy
import matplotlib.pyplot as plt
from queryutils.databases import PostgresDB, SQLite3DB
from queryutils.parse import tokenize_query
from queryutils.splunktypes import lookup_categories

SOURCES = {
    "postgresdb": (PostgresDB, ["database", "user", "password"]),
    "sqlite3db": (SQLite3DB, ["srcpath"])
}

class QueryType(object):
    INTERACTIVE = "interactive"
    SCHEDULED = "scheduled"

def main(source, query_type, user_weighted, output):
    stage_pcts, nstages, query_pcts, nqueries = tally(source, query_type, user_weighted)
    label = "weighted" if user_weighted else "unweighted"
    output = "%s-%s" % (output, label)
    stages_textbox = "%.1f stages per user" if user_weighted else "%d stages"
    queries_textbox = "%.1f queries per user" if user_weighted else "%d queries"
    stages_textbox = stages_textbox % nstages
    queries_textbox = queries_textbox % nqueries
    plot_barchart(stage_pcts, stages_textbox, query_pcts, queries_textbox, output)

def tally(source, query_type, user_weighted):
    if user_weighted:
        return tally_weighted(source, query_type)
    else:
        return tally_unweighted(source, query_type)

def tally_weighted(source, query_type):

    stage_cnt = {}
    nstages = 0
    nstages_per_user = defaultdict(int)

    query_cnt = {}
    nqueries = 0
    nqueries_per_user = defaultdict(int)
    all_transforms = set()

    for (user, query) in fetch_queries_by_user(source, query_type):

        transforms = lookup_categories(query)

        nstages += len(transforms)
        nstages_per_user[user] += len(transforms)
        nqueries += 1
        nqueries_per_user[user] += 1

        if not user in stage_cnt:
            stage_cnt[user] = defaultdict(int)
        if not user in query_cnt:
            query_cnt[user] = defaultdict(int)
        
        for t in transforms:
            stage_cnt[user][t] += 1
        for t in set(transforms):
            all_transforms.add(t)
            query_cnt[user][t] += 1

    stage_pct = defaultdict(list)
    for (user, transform_counts) in stage_cnt.iteritems():
        user_nstages = float(sum(transform_counts.values()))
        assert user_nstages == nstages_per_user[user]
        for t in all_transforms:
            count = transform_counts.get(t, 0.)
            user_pct = count / user_nstages
            stage_pct[t].append(user_pct)
    stage_pct = { t: numpy.mean(pcts) for (t, pcts) in stage_pct.iteritems() }

    query_pct = defaultdict(list)
    for (user, transform_counts) in query_cnt.iteritems():
        user_nquerys = float(nqueries_per_user[user])
        for t in all_transforms:
            count = transform_counts.get(t, 0.)
            user_pct = count / user_nquerys
            query_pct[t].append(user_pct)
    query_pct = { t: numpy.mean(pcts) for (t, pcts) in query_pct.iteritems() }

    nstages_per_user = numpy.mean(nstages_per_user.values())
    nqueries_per_user = numpy.mean(nqueries_per_user.values())
    return stage_pct, nstages_per_user, query_pct, nqueries_per_user

def tally_unweighted(source, query_type):

    stage_cnt = defaultdict(int)
    nstages = 0

    query_cnt = defaultdict(int)
    nqueries = 0
    
    for query in fetch_queries(source, query_type):

        transforms = lookup_categories(query)

        nstages += len(transforms)
        nqueries += 1
        
        for t in transforms:
            stage_cnt[t] += 1
        for t in set(transforms):
            query_cnt[t] += 1
    
    stage_pct = { t: float(cnt)/nstages for (t, cnt) in stage_cnt.iteritems() }
    query_pct = { t: float(cnt)/nqueries for (t, cnt) in query_cnt.iteritems() }

    return stage_pct, nstages, query_pct, nqueries

def fetch_queries_by_user(source, query_type):
    source.connect()
    if query_type == QueryType.INTERACTIVE:
        ucursor = source.execute("SELECT id FROM users WHERE user_type is null")
    elif query_type == QueryType.SCHEDULED:
        ucursor = source.execute("SELECT id FROM users")
    else:
        raise RuntimeError("Invalid query type.")
    for row in ucursor.fetchall():
        user_id = row["id"]
        if query_type == QueryType.INTERACTIVE:
            sql = "SELECT text FROM queries WHERE is_interactive=true AND is_suspicious=false AND user_id=%s" % source.wildcard
        elif query_type == QueryType.SCHEDULED:
            sql = "SELECT DISTINCT text FROM queries WHERE is_interactive=false AND user_id=%s" % source.wildcard
        else:
            raise RuntimeError("Invalid query type.")
        qcursor = source.execute(sql, (user_id, )) 
        for row in qcursor.fetchall():
            query = row["text"]
            yield (user_id, query)
    source.close()

def fetch_queries(source, query_type):
    source.connect()
    if query_type == QueryType.INTERACTIVE:
        sql = "SELECT text FROM queries, users \
                WHERE queries.user_id=users.id AND \
                    is_interactive=true AND \
                    is_suspicious=false AND \
                    user_type is null"
    elif query_type == QueryType.SCHEDULED:
        sql = "SELECT DISTINCT text FROM queries WHERE is_interactive=false"
    else:
        raise RuntimeError("Invalid query type.")
    cursor = source.execute(sql)
    for row in cursor.fetchall():
        yield row["text"]
    source.close()

def plot_barchart(stage_percents, stages_label, query_percents, queries_label, output):
   
    spcts = sorted(stage_percents.iteritems(), key=lambda x: x[1], reverse=True)
    names = [k for (k,v) in spcts]
    qpcts = [query_percents[k]*100 for (k,v) in spcts]
    spcts = [v*100 for (k,v) in spcts]
    for (n, s, q) in zip(names, spcts, qpcts):
        print "%s, %.1f, %.1f" % (n, s, q)
    
    index = numpy.arange(len(stage_percents))

    plt.subplot(2, 1, 1)
    plt.bar(index, spcts, 1, color="r")
    plt.ylabel("% stages", fontsize=18)
    plt.yticks(range(0, 100, 10), fontsize=12)
    plt.xticks(index + 0.5, ["" for n in names])
    plt.text(10.5, 72, "N = %s" % stages_label,
        fontsize=16, bbox=dict(facecolor="none", edgecolor="black", pad=10.0))
    plt.tick_params(bottom="off")
    
    plt.subplot(2, 1, 2)
    plt.bar(index, qpcts, 1, color="c")
    plt.ylabel("% queries", fontsize=18)
    plt.yticks(range(0, 100, 10), fontsize=12)
    plt.xticks(index + 0.5, names, rotation=-45, fontsize=16,
       rotation_mode="anchor", ha="left")
    #plt.xlabel("Transformation Type", fontsize=20)
    plt.text(10, 80, "N = %s" % queries_label,
             fontsize=16, bbox=dict(facecolor="none", edgecolor="black", pad=10.0))
    plt.tick_params(bottom="off")

    plt.autoscale(enable=True, axis="x", tight=None)
    plt.tight_layout()
    plt.savefig(output + ".pdf", dpi=400)

def lookup(dictionary, lookup_keys):
    return [dictionary[k] for k in lookup_keys]

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Bar graph describing how frequently each transformation appears in user queries.")
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
    parser.add_argument("-q", "--querytype",
                        help="the type of queries (scheduled or interactive)")
    parser.add_argument("-w", "--weighted", action="store_true",
                        help="if true, average across users")
    args = parser.parse_args()
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
