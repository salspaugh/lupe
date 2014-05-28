from logging import DEBUG, getLogger as get_logger
from logging.handlers import RotatingFileHandler
from time import time

logger = get_logger("lupe")
start = time()

from argparse import ArgumentParser
from clustering import spectral, kmedoids
from json import dump
from featurize import get_features, featurize_obj
from numpy import linalg, cov, argsort, dot, empty, zeros, array, max, abs, isnan
from os import path, walk
from queryutils.datasource import CSVFiles, JSONFiles, PostgresDB, SQLite3DB
from tsnewrapper import calc_tsne

import csv
import pylab

elapsed = time() - start
logger.debug("[pipeline] - Time to import (seconds): " + str(elapsed))

PERPLEXITY = 50

class Clusterees(object):

    QUERIES = "queries"
    SESSIONS = "sessions"
    FILTERS = "filters"
    AUGMENTS = "augments"
    AGGREGATES = "aggregates"


def fetch_data(source, clusterees):
    logger.debug("[pipeline] - Fetching data.")
    start = time()
    data = None
    fetchers = {
        Clusterees.SESSIONS: (source.get_sessions, label_session),
        Clusterees.FILTERS: (source.get_unique_filters, label_parsetree),
        Clusterees.AUGMENTS: (source.get_unique_augments, label_parsetree),
        Clusterees.AGGREGATES: (source.get_unique_aggregates, label_parsetree),
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


def normalize_points(points):
    logger.debug("[pipeline] - Normalize.")
    start = time()
    p = array(points) * 1.
    p /= max(abs(p), axis=0)
    p[isnan(p)] = 0.
    logger.debug("[pipeline] - Time to normalize (seconds): " + str(elapsed))
    return p


def run_pipeline(pipeline, nclusters, points, outputclusters, clusterer, pcadims):
    pipelines = {
        1: pipeline1,
        2: pipeline2,
        3: pipeline3,
        4: pipeline4,
        5: pipeline5,
        6: pipeline6,
        7: pipeline7,
        8: pipeline8,
        9: pipeline9
    }
    pipeline = pipelines.get(pipeline, None)
    if pipeline is None:
        raise RuntimeError("No such pipeline.")
    return pipeline(points, outputclusters, nclusters, clusterer, pcadims)


def pipeline1(points, outputclusters, nclusters, clusterer, *args, **kwargs):
    clusters, centers = cluster(points, nclusters, clusterer)
    projected_points = tsne(points)
    return clusters, projected_points


def pipeline2(points, outputclusters, nclusters, clusterer, pcadims):
    clusters, centers = cluster(points, nclusters, clusterer)
    after_pca_points = pca(points, pcadims)
    projected_points = tsne(after_pca_points)
    return clusters, projected_points


def pipeline3(points, outputclusters, nclusters, clusterer, pcadims):
    after_pca_points = pca(points, pcadims)
    clusters, centers = cluster(points, nclusters, clusterer)
    projected_points = tsne(after_pca_points)
    return clusters, projected_points


def pipeline4(points, outputclusters, nclusters, clusterer, pcadims):
    after_pca_points = pca(points, pcadims)
    clusters, centers = cluster(points, nclusters, clusterer)
    projected_points = pca(points, 2)
    return clusters, projected_points


def pipeline5(points, outputclusters, nclusters, clusterer, *args, **kwargs):
    clusters, centers = cluster(points, nclusters, clusterer)
    projected_points = pca(points, 2)
    return clusters, projected_points


def pipeline6(points, outputclusters, nclusters, clusterer, *args, **kwargs):
    projected_points = tsne(points)
    clusters, centers = cluster(projected_points, nclusters, clusterer)
    return clusters, projected_points


def pipeline7(points, outputclusters, nclusters, clusterer, pcadims):
    after_pca_points = pca(points, pcadims)
    projected_points = tsne(after_pca_points)
    clusters, centers = cluster(projected_points, nclusters, clusterer)
    return clusters, projected_points


def pipeline8(points, outputclusters, *args, **kwargs):
    projected_points = tsne(points)
    labels = zeros(len(projected_points))
    return labels, projected_points


def pipeline9(points, outputclusters, *args, **kwargs):
    pcadims = args[-1]
    after_pca_points = pca(points, pcadims)
    projected_points = tsne(after_pca_points)
    labels = zeros(len(projected_points))
    return labels, projected_points


def cluster(points, k, clusterer):
    if clusterer == "spectral":
        return spectral(points, k)
    elif clusterer == "kmedoids":
        return kmedoids(points, k)
    else:
        raise RuntimeError("No valid clustering method chosen.")


def pca(data, dimensions):
    data = array(data)
    new = data - data.mean(axis=0)
    if new.shape[1] < dimensions:
        dimensions = new.shape[1]
    (eig_values, eig_vectors) = linalg.eig(cov(new.T))
    perm = argsort(-eig_values)
    eig_vectors = eig_vectors[:, perm[0:dimensions]]
    new = dot(new, eig_vectors)
    return new


def tsne(points):
    points = array(points)  # Make sure that points is a numpy array.
    return calc_tsne(points, no_dims=2, perplexity=PERPLEXITY, landmarks=1)


def output_clusters(ids, clusters, filename):
    csvfile = ".".join([filename, "csv"])
    with open(csvfile, 'w') as clusterfile:
        writer = csv.writer(clusterfile)
        for (point_id, cluster_id) in zip(ids, clusters):
            writer.writerow([point_id, cluster_id])


def plot(points, labels, filename):
    pngfile = ".".join([filename, "png"])
    pylab.scatter(points[:, 0], points[:, 1], 20, labels)
    pylab.savefig(pngfile)


def output_visualization_data(points, labels, mouseovers, filename):
    d3data = ".".join([filename, "d3.csv"])
    with open(d3data, 'w') as d3data:
        writer = csv.writer(d3data)
        writer.writerow(["cluster", "X", "Y", "mouseover"])
        for (cluster, point, mouseover) in zip(labels, points, mouseovers):
            row = [cluster] + list(point) + [mouseover]
            writer.writerow(row)


def get_feature_modules():
    this_dir = path.dirname(path.realpath(__file__))
    features_dir = path.join(this_dir, "features")
    features = []
    for (dirpath, dirnames, filenames) in walk(features_dir):
        for filename in filenames:
            if not filename == "__init__.py" and filename[-3:] == ".py":
                features.append(filename[:-3])
    return features
