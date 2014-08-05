from featurize import get_features, featurize_obj
from json import dump
from logging import getLogger as get_logger
from os import path, walk
from time import time

logger = get_logger("lupe")

class Clusterees(object):

    QUERIES = "queries"
    SESSIONS = "sessions"
    FILTERS = "filters"
    AUGMENTS = "augments"
    AGGREGATES = "aggregates"
    QUERYGROUPS = "querygroups"


def fetch_data(source, clusterees):
    logger.debug("[pipeline] - Fetching data.")
    start = time()
    data = None
    fetchers = {
        Clusterees.SESSIONS: (source.get_sessions, label_session),
        Clusterees.FILTERS: (source.get_unique_filters, label_parsetree),
        Clusterees.AUGMENTS: (source.get_unique_augments, label_parsetree),
        Clusterees.AGGREGATES: (source.get_unique_aggregates, label_parsetree),
        Clusterees.QUERYGROUPS: (source.get_query_groups, label_query_group),
    }
    fetcher = fetchers.get(clusterees, None)
    if fetcher is None:
        raise RuntimeError(
            "No valid set of objects to cluster over has been chosen.")
    fetch = fetcher[0]
    label = fetcher[1]
    data = []
    mouseovers = []
    for d in fetch():
        data.append(d)
        mouseovers.append(label(d))
    data = [d for d in data if d is not None]
    elapsed = time() - start 
    logger.debug("[pipeline] - Time to fetch data (seconds): " + str(elapsed))
    logger.debug("[pipeline] - Rows of data fetched: " + str(len(data)))
    return data, mouseovers


def label_session(session):
    label = ["User: " + session.user.name]
    for query in session.queries:
        label.append("".join([str(int(round(query.time))), "\t", wrap_text(query.text)]))
    return "\n".join(label)


def label_parsetree(node):
    return node.str_tree()


def label_query_group(querygroup):
    return str(querygroup)


def output_mouseovers(mouseovers, filename):
    filename = ".".join([filename, "json"])
    with open(filename, 'w') as f:
        dump(mouseovers, f, sort_keys=True, indent=4, separators=(',', ': '))


def featurize(objects, features):
    logger.debug("[pipeline] - Computing features.")
    start = time()
    features = get_features(features)
    feature_vectors = [fid + feature_vector for (fid, feature_vector) in
                       [([obj.id], featurize_obj(obj, features))
                        for obj in objects]
                       if feature_vector is not None]
    if not feature_vectors:
        raise RuntimeError(
            "Featurizing was unsuccessful -- no features computed.")
    elapsed = time() - start 
    logger.debug("[pipeline] - Time to featurize (seconds): " + str(elapsed))
    f = feature_vectors[0]
    logger.debug("[pipeline] - Number of features per object computed: " + str(len(f)))
    return feature_vectors


def output_features(feature_vectors, filename):
    filename = ".".join([filename, "csv"])
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        for v in feature_vectors:
            writer.writerow(v)


def fetch_features(filename):
    logger.debug("[pipeline] - Fetching features.")
    start = time()
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        features = [[float(r) for r in row] for row in reader]
    elapsed = time() - start 
    logger.debug("[pipeline] - Time to fetch features (seconds): " + str(elapsed))
    logger.debug("[pipeline] - Number of vectors fetched: " + str(len(features)))
    logger.debug("[pipeline] - Number of features per vector: " + str(len(features[0])))
    return features


def fetch_mouseovers(filename):
    logger.debug("[pipeline] - Fetching mouseover labels.")
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        mouseovers = [mouseover for (mouseover, ) in reader]
    return mouseovers


