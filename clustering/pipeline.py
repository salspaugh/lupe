from logging import getLogger as get_logger
from time import time

logger = get_logger("lupe")
start = time()

from clustering import spectral, kmedoids
from numpy import linalg, cov, argsort, dot, empty, zeros, array, max, abs, isnan
from tsnewrapper import calc_tsne

import csv
import json
import pylab

elapsed = time() - start
logger.debug("[pipeline] - Time to import (seconds): " + str(elapsed))

PERPLEXITY = 50
NON_PCA_PIPELINES = [1, 5, 6, 8]
PCA_PIPELINES = [2, 3, 4, 7, 9]


def main(inputpoints, inputmouseovers, outputclusters, pipeline, nclusters, clusterer, pcadims, normalize):
    features = read_points(inputpoints)
    points = [feature[1:] for feature in features]  # Exclude the object ID.
    ids = [feature[0] for feature in features] # The object IDs.
    if normalize:
        points = normalize_points(points)
    mouseovers = read_mouseovers(inputmouseovers) 
    clusters, projected_points = run_pipeline(pipeline, nclusters, points, outputclusters, clusterer, pcadims)
    output_clusters(ids, clusters, outputclusters)
    plot(projected_points, clusters, outputclusters)
    output_visualization_data(projected_points, clusters, mouseovers, outputclusters)
    output_projected_points(ids, projected_points, features)

def read_points(input):
    points = []
    with open(input) as inputpoints:
        reader = csv.reader(inputpoints)
        for row in reader:
            vector = []
            for elem in row:
                feature = -1.
                try:
                    feature = float(elem)
                except:
                    logger.debug("[pipeline] - Error casting feature element to float.")
                vector.append(feature)
            points.append(vector)
        return points


def read_mouseovers(input):
    with open(input) as inputmouseovers:
        reader = csv.reader(inputmouseovers)
        mouseovers = [row[0] for row in reader]
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

def output_projected_points(ids, points, features, filename):
    fn = ".".join([filename, "projected-points.json"])
    data = []
    for i, p, f in zip(ids, points, features):
        obj = {}
        obj["id"] = i
        obj["point"] = p
        obj["features"] = f
        data.append(obj)
    with open(fn, 'w') as f:
        json.dump(f, data)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser("Project and cluster points.")
    parser.add_argument("-i", "--points",
                        help="REQUIRED: the data points in .csv format to project and cluster (first column is id)")
    parser.add_argument("-m", "--mouseovers",
                        help="REQUIRED: the mouseover labels in .csv format for the data points")
    parser.add_argument("-o", "--clusters",
                        help="the output filename to write the cluster assingments (default: clusters)")
    parser.add_argument("-p", "--pipeline", type=int,
                        help="REQUIRED: pipeline to run. \
                        (pipelines: \
                            [1: cluster, t-SNE], \
                            [2: cluster, PCA, t-SNE], \
                            [3: PCA, cluster, t-SNE], \
                            [4: PCA, cluster, PCA], \
                            [5: cluster, PCA], \
                            [6: t-SNE, cluster], \
                            [7: PCA, t-SNE, cluster] \
                            [8: t-SNE] \
                            [9: PCA, t-SNE]")
    parser.add_argument("-k", "--nclusters", type=int,
                        help="number of clusters to look for (default: 4)")
    parser.add_argument("-c", "--clusterer",
                        help="method to use for clustering (options: spectral, kmedoids; default: kmedoids)")
    parser.add_argument("-d", "--pcadims", type=int,
                        help="dimensions to reduce to via PCA (default: None)")
    parser.add_argument("-n", "--normalize", action="store_true",
                        help="whether or not to normalize (default: False)")
    
    args = parser.parse_args()
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()

    if not args.points:
        raise RuntimeError("You must specify input points.")
    if not args.mouseovers:
        raise RuntimeError("You must specify mouse-over points.")
    if not args.pipeline:
        raise RuntimeError("You must specify a pipeline to run.")
    if not args.nclusters:
        args.nclusters = 4
    if not args.clusterer:
        args.clusterer = "kmedoids"
    
    if (args.pipeline in NON_PCA_PIPELINES) and args.pcadims is not None:
        raise RuntimeWarning(
            "Incompatible option specified: PCA is not used with this pipeline.")
    if (args.pipeline in PCA_PIPELINES) and args.pcadims is None:
        raise RuntimeWarning(
            "You need to specify the number of dimensions to reduce to using PCA (using the -d flag).")


    main(args.points, args.mouseovers, args.clusters, 
        args.pipeline, args.nclusters, args.clusterer, args.pcadims, args.normalize)
