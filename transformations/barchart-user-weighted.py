from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
from queryutils.databases import PostgresDB, SQLite3DB
from queryutils.files import CSVFiles, JSONFiles
from queryutils.parse import tokenize_query
from queryutils.splunktypes import lookup_categories

SOURCES = {
    "postgresdb": (PostgresDB, ["database", "user", "password"]),
    "sqlite3db": (SQLite3DB, ["srcpath"])
}

class QueryType(object):
    INTERACTIVE = "interactive"
    SCHEDULED = "scheduled"

def main(source, query_type, output, user_weighted):
    tfm_by_user, cmd_by_user = tally_all(source, query_type)
    tfm_agg = aggregate_transforms(tfm_by_user, user_weighted)
    cmd_agg = aggregate_commands(cmd_by_user, user_weighed)
    print_transformation_data(tfm_agg, output)
    print_command_data(cmd_agg, output)

def tally_all(source, querytype):

    stage_cnt = {}
    query_tfm_cnt = {}
    query_cmd_cnt = {}
    tfm_dicts = [stage_cnt, query_tfm_cnt, query_cmd_cnt]

    stage_cmd_cnt = {}
    query_tfm_cmd_cnt = {}
    query_cmd_cmd_cnt = {}
    cmd_dicts = [stage_cmd_cnt, query_tfm_cmd_cnt, query_cmd_cmd_cnt]

    nstages = nqueries = 0

    for (user, query) in fetch_data(source, querytype):

        init_dictionaries(user, tfm_dicts, cmd_dicts)

        transforms = lookup_categories(query)
        commands = lookup_commands(query)

        # Number of stages per user of each type.
        tfms_cmds = dict(zip(transforms, commands)).items()
        tally_one(user, stage_cnt, stage_cmd_cnt, tfms_cmds)
        
        # Number of queries per user of each transform type.
        # Command selected arbitrarily.
        uniq_tfm = dict(zip(transforms, commands)).items()
        tally_one(user, query_tfm_cnt, query_tfm_cmd_cnt, uniq_tfm)
        
        # Number of queries per user of each command.
        # Some transforms will be double-counted.
        uniq_cmd = [(y,x) for (x,y) in dict(zip(commands, transforms)).items()]
        tally_one(user, query_cmd_cnt, query_cmd_cmd_cnt, uniq_cmd)
    
    return tfm_dicts, cmd_dicts

def fetch_data(source, querytype):
    source.connect()
    cursor = source.execute("SELECT id FROM users WHERE user_type is null LIMIT 20")
    for row in cursor.fetchall():
        user_id = row["id"]
        if querytype == QueryType.INTERACTIVE:
            sql = "SELECT text FROM queries WHERE is_interactive=true AND is_suspicious=false"
        elif querytype == QueryType.SCHEDULED:
            sql = "SELECT DISTINCT text FROM queries WHERE is_interactive=false AND user_id=%s" % source.wildcard
        else:
            raise RuntimeError("Invalid query type.")
        cursor = source.execute(sql, user_id) 
        for row in cursor.fetchall():
            query = row["text"]
            yield (user_id, query)
    source.close()

def init_dictionaries(key, tfm_dicts, cmd_dicts):
    for d in tfm_dicts:
        init_defaultdict_int(key, d)
    for d in cmd_dicts:
        init_dict(key, d)

def init_defaultdict_int(key, dct):
    if not key in dct:
        dct[key] = defaultdict(int)

def init_dict(key, dct):
    if not key in dct:
        dct[key] = {}

def lookup_commands(querystring):
    commands = []
    tokens = tokenize_query(querystring)
    for token in tokens:
        val = token.value.strip().lower()
        if token.type == "EXTERNAL_COMMAND":
            commands.append(val)
        elif token.type == "MACRO":
            commands.append(val)
        elif token.type not in ["ARGS", "PIPE", "LBRACKET", "RBRACKET"]:
            commands.append(val)
    return commands

def tally_one(user, tfm_cnt, cmd_cnt, tfms_cmds):
    for (tfm, cmd) in tfms_cmds:
        tfm_cnt[user][tfm] += 1
        if not tfm in cmd_cnt[user]:
            cmd_cnt[user][tfm] = defaultdict(int)
        cmd_cnt[user][tfm][cmd] += 1

def aggregate_transformation_percents_weighted(tfm_cnts_by_user):
    tfm_pcts = defaultdict(list)
    for (user, tfm_cnts) in tfm_cnts_by_user.iteritems():
        total = float(sum(tfm_cnts.values()))
        for tfm, cnt in tmf_cnts.iteritems():
            pct = float(cnt) / total
            tfm_pcts[tfm].append(pct)
    tfm_pcts = { tfm: mean(pcts) for (tfm, pct) in tfm_pcts.iteritems() }
    return tfm_pcts

def aggregate_transformation_counts_weighted(tfm_cnts_by_user):
    tfm_cnts = defaultdict(list)
    for (user, cnts) in tfm_cnts_by_user.iteritems():
        for tfm, cnt in cnts.iteritems():
            tfm_cnts[tfm].append(cnt)
    tfm_cnts = { tfm: mean(cnt) for (tfm, pct) in tfm_pcts.iteritems() }
    return tfm_cnts

def aggregate_transformation_percents_unweighted(tfm_cnts_by_user):
    tfm_pcts = defaultdict(int) 
    for (user, cnts) in tfm_cnts_by_user.iteritems():
        total = float(sum(cnts.values()))
        for tfm, cnt in cnts.iteritems():
            tfm_pcts[tfm] = float(cnt) / total
    return tfm_pcts

def aggregate_transformation_counts_unweighted(tfm_cnts_by_user):
    tfm_cnts = defaultdict(int) 
    for (user, cnts) in tfm_cnts_by_user.iteritems():
        for tfm, cnt in cnts.iteritems():
            tfm_cnts[tfm] += cnt
    return tfm_cnts

def aggregate_command_percents_weighted(tfm_cmd_cnts_by_user):
    tfm_cmd_pcts = {}
    for (user, tfm_cmd_cnts) in tfm_cmd_cnts_by_user.iteritems():
        for (tfm, cmd_cnts) in tfm_cmd_cnts.iteritems():
            if not tfm in tfm_cmd_pcts:
                tfm_cmd_pcts[tfm] = defaultdict(list)
            total = float(sum(cmd_cnts.values()))
            for (cmd, cnt) in cmd_cnts.iteritems():
                pct = float(cnt) / total
                tfm_cmd_pcts[tfm][cmd].append(pct)
    for (tfm, cmd_pcts) in tfm_cmd_pcts.iteritems():
        tfm_cmd_pcts[tfm] = { cmd: mean(pcts) for (cmd, pct) in cmd_pcts.iteritems() }
    return tfm_cmd_pcts 

def aggregate_command_counts_weighted(tfm_cmd_cnts_by_user):
    tfm_cmd_cnts_agg = {}
    for (user, tfm_cmd_cnts) in tfm_cmd_cnts_by_user.iteritems():
        for (tfm, cmd_cnts) in tfm_cmd_cnts.iteritems():
            if not tfm in tfm_cmd_cnts_agg:
                tfm_cmd_cnts_agg[tfm] = defaultdict(list)
            total = float(sum(cmd_cnts.values()))
            for (cmd, cnt) in cmd_cnts.iteritems():
                tfm_cmd_cnts_agg[tfm][cmd].append(cnt)
    for (tfm, cmd_cnts) in tfm_cmd_cnts_agg.iteritems():
        tfm_cmd_cnts_agg[tfm] = { cmd: mean(cnts) for (cmd, cnts) in cmd_cnts.iteritems() }
    return tfm_cmd_cnts_agg

def aggregate_command_percents_unweighted(tfm_cmd_cnts_by_user):
    tfm_cmd_pcts = {}
    for (user, tfm_cmd_cnts) in tfm_cmd_cnts_by_user.iteritems():
        for (tfm, cmd_cnts) in tfm_cmd_cnts.iteritems():
            if not tfm in tfm_cmd_pcts:
                tfm_cmd_pcts[tfm] = defaultdict(int)
            for (cmd, cnt) in cmd_cnts.iteritems():
                tfm_cmd_pcts[tfm][cmd] += cnt
    for (tfm, cmd_cnts) in tfm_cmd_pcts.iteritems():
        total = float(sum(tfm_cmd_pcts[tfm].values()))
        for (cmd, cnt) in cmd_cnts.iteritems():
            tfm_cmd_pcts[tfm][cmd] = float(cnt) / total
    return tfm_cmd_pcts

def aggregate_command_counts_unweighted(tfm_cmd_cnts_by_user):
    tfm_cmd_cnts_agg = {}
    for (user, tfm_cmd_cnts) in tfm_cmd_cnts_by_user.iteritems():
        for (tfm, cmd_cnts) in tfm_cmd_cnts.iteritems():
            if not tfm in tfm_cmd_cnts_agg:
                tfm_cmd_cnts_agg[tfm] = defaultdict(int)
            for (cmd, cnt) in cmd_cnts.iteritems():
                tfm_cmd_cnts_agg[tfm][cmd] += cnt
    return tfm_cmd_cnts_agg

def aggregate_transforms(tfm_cnts_by_user, weighted):
    aggregate_counts = aggregate_transformation_counts_weighted
    aggregate_percents = aggregate_transformation_percents_weighted
    if not weighted:
        aggregate_counts = aggregate_transformation_counts_unweighted
        aggregate_percents = aggregate_transformation_percents_unweighted
    return aggregate(aggregate_counts, aggregate_percents, tfm_cnts_by_user)

def aggregate_commands(cmd_cnts_by_user, weighted):
    aggregate_counts = aggregate_command_counts_weighted
    aggregate_percents = aggregate_command_percents_weighted
    if not weighted:
        aggregate_counts = aggregate_command_counts_unweighted
        aggregate_percents = aggregate_command_percents_unweighted
    return aggregate(aggregate_counts, aggregate_percents, cmd_cnts_by_user) 

def aggregate(aggregate_counts, aggregate_percents, cnts_by_user):
    (stage_cnts_by_user, query_tfm_cnts_by_user, query_cmd_cnts_by_user) = cnts_by_user
    stage_cnts = aggregate_counts(stage_cnts_by_user)
    query_tfm_cnts = aggregate_counts(query_tfm_cnts_by_user)
    query_cmd_cnts = aggregate_counts(query_cmd_cnts_by_user)
    stage_pcts = aggregate_percents(stage_cnts_by_user)
    query_tfm_pcts = aggregate_percents(query_tfm_cnts_by_user)
    query_cmd_pcts = aggregate_percents(query_cmd_cnts_by_user)
    return (stage_cnts, query_tfm_cnts, query_cmd_cnts, stage_pcts, query_tfm_pcts, query_cmd_pcts) 

def print_transformation_data(tfm_aggregated, output, weighted):
    out = "%s-weighted-transformation-counts.txt" % output
    if not weighted:
        out = "%s-unweighted-transformation-counts.txt" % output

    (stage_cnts, query_tfm_cnts, query_cmd_cnts, stage_pcts, query_tfm_pcts, query_cmd_pcts) = tfm_aggregated 
    transforms = [k for (k,v) in sorted(stage_cnts.iteritems(), key=lambda x: x[1], reverse=True)]

    header = ("transformation", "nstages", "%stages", "nqueries-tfm", "%queries-tfm", "nqueries-cmd", "%queries-cmd")
    with open(out, "w") as out:
        out.write("%16s %14s %14s %14s %14s %14s %14s\n" % header)
        for t in transforms:
            line = (t, stage_cnts[t], stage_pcts[t], query_tfm_cnts[t], query_tfm_pcts[t], query_cmd_cnts[t], query_cmd_pcts[t])
            out.write("%16s %12d %12.3f %12d %12.3f %12d %12.3f\n" % line)

def print_command_data(cmd_aggregated, output, weighted):

    out = "%s-weighted-command-counts.txt" % output
    if not weighted:
        out = "%s-unweighted-command-counts.txt" % output

    (stage_cmd_cnts, query_tfm_cmd_cnts, query_cmd_cmd_cnts, stage_cmd_pcts, query_tfm_cmd_pcts, query_cmd_cmd_pcts) = cmd_aggregated

    header = ("transformation", "command", "nstages", "%stages", "nqueries-tfm", "%queries-tfm", "nqueries-cmd", "%queries-cmd")
    with open(out, "w") as out:
        out.write("%16s %30s %14s %14s %14s %14s %14s %14s\n" % header)
        for (t, cmd_stats) in stage_cmd_cnts.iteritems():
            cmds = [k for (k, v) in sorted(cmd_stats.iteritems(), key=lambda x: x[1], reverse=True)]
            for c in cmds:
                line = (t, c, stage_cmd_cnts[t][c], stage_cmd_pcts[t][c], 
                              query_tfm_cmd_cnts[t][c], query_tfm_cmd_pcts[t][c],
                              query_cmd_cmd_cnts[t][c], query_cmd_cmd_pcts[t][c]) 
                out.write("%16s %30s %12d %12.2f %12d %12.2f %12d %12.2f\n" % line)

def create_histogram(stages_per_transformation, queries_per_transformation, nqueries, output):
    nstages = float(sum(stages_per_transformation.values()))
    nqueries = float(nqueries)

    spcts = { k: v/nstages*100 for (k,v) in stages_per_transformation.iteritems() }
    qpcts = { k: v/nqueries*100 for (k,v) in queries_per_transformation.iteritems() }
    spcts = sorted(spcts.iteritems(), key=lambda x: x[1], reverse=True)
    names = [k for (k,v) in spcts]
    qpcts = [qpcts[k] for (k,v) in spcts]
    spcts = [v for (k,v) in spcts]

    #fig = plt.figure(figsize=(13.5, 8.0))
    index = np.arange(len(stages_per_transformation))

    print "transformation, % stages, % queries"
    for (n, s, q) in zip(names, spcts, qpcts):
        print "%s, %f, %f" % (n, s, q)
    
    plt.subplot(2, 1, 1)
    plt.bar(index, spcts, 1, color="r")
    plt.ylabel("% stages", fontsize=18)
    plt.yticks(range(0, 100, 10), fontsize=12)
    plt.xticks(index + 0.5, ["" for n in names])
    plt.text(12, 72, "N = " + str(int(nstages)) + " stages",
        fontsize=16, bbox=dict(facecolor="none", edgecolor="black", pad=10.0))
    plt.tick_params(bottom="off")
    
    plt.subplot(2, 1, 2)
    plt.bar(index, qpcts, 1, color="c")
    plt.ylabel("% queries", fontsize=18)
    plt.yticks(range(0, 100, 10), fontsize=12)
    plt.xticks(index + 0.5, names, rotation=-45, fontsize=16,
       rotation_mode="anchor", ha="left")
    #plt.xlabel("Transformation Type", fontsize=20)
    plt.text(12, 80, "N = " + str(int(nqueries)) + " queries",
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
    main(source, args.querytype, args.output, args.weighted)
