from logging import getLogger, basicConfig, DEBUG
from logging.handlers import RotatingFileHandler
import logging
import queryutils

BYTES_IN_MB = 1048576
FIVE_MB = 5*BYTES_IN_MB

logger = getLogger("lupe")
logger.setLevel(DEBUG)
handler = RotatingFileHandler("lupe.log", maxBytes=FIVE_MB)
handler.setLevel(DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

from argparse import ArgumentParser
from data import *
from pipeline import *
from queryutils.arguments import lookup, SOURCES

# Uncomment to debug:
# from numpy import seterr
# seterr(all="raise")

NON_PCA_PIPELINES = [1, 5, 6, 8]
PCA_PIPELINES = [2, 3, 4, 7, 9]

def get_args():

    # We're using optional arguments above but nonetheless some of them are required.
    # We prefer optional arguments because the letters are useful mnemonics
    # and position doesn't matter.

    feature_options = ", ".join(get_feature_modules())
    object_options = [x for x in dir(Clusterees)
        if not x[:2] == "__" and not x[:-2] == "__"]
    object_options = [getattr(Clusterees, x) for x in object_options]
    object_options = ", ".join(object_options)

    parser = ArgumentParser()

    parser.add_argument("-p", "--pipeline",
                        help="REQUIRED! Pipeline to run. \
                        Pipelines are: \
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
                        help="REQUIRED! Number of clusters to look for.")
    parser.add_argument("-f", "--features", nargs='+',
                        help="REQUIRED! What features to use. \
                            This should be compatible with the choice of object. \
                            Can be one of: " + feature_options)
    parser.add_argument("-l", "--clusterees",
                        help="REQUIRED! What type of object to cluster. \
                            This should be compatible with the choice of features. \
                            Can be one of: " + object_options)
    parser.add_argument("-c", "--clusterer",
                        help="Method used to cluster. Default is spectral clustering.")
    parser.add_argument("-d", "--pcadimension", type=int,
                        help="Dimension to reduce feature space down to when using PCA. \
                            Not applicable for all pipelines.")
    parser.add_argument("-n", "--normalize", action="store_true",
                        help="Whether or not to normalize. \
                            If this flag is used, features will be normalized. \
                            Default is false.")
    parser.add_argument("-o", "--outputclusters",
                        help="Name of the output plot (.png format) and \
                            cluster assignments (.csv format). \
                            Default name is 'output' with appropriate extensions.")
    parser.add_argument("-t", "--outputfeatures",
                        help="Name of the output file containing \
                            raw features vectors (.csv format).")
    parser.add_argument("-u", "--outputmouseovers",
                        help="Name of the output file containing \
                            raw mouseovers vectors (.csv format).")
    parser.add_argument("-i", "--inputfeatures",
                        help="Name of the input file containing \
                            raw features vectors (.csv format).")
    parser.add_argument("-m", "--inputmouseovers",
                        help="Name of the input file containing \
                            raw mouseovers vectors (.csv format).")
    args = queryutils.arguments.get_arguments(parser)
   
    if all([arg is None for arg in vars(args).values()]):
        parser.print_help()
        exit()
    return args

def get_feature_modules():
    this_dir = path.dirname(path.realpath(__file__))
    features_dir = path.join(this_dir, "features")
    features = []
    for (dirpath, dirnames, filenames) in walk(features_dir):
        for filename in filenames:
            if not filename == "__init__.py" and filename[-3:] == ".py":
                features.append(filename[:-3])
    return features

def check_args(args):

    # TODO: Make sure the proper arguments for the given source are passed in.
    if not args.source:
        raise RuntimeError(
            "You must specify where to fetch the data and the corresponding arguments (-s or --source).")
    if not args.pipeline:
        raise RuntimeError(
            "You must specify a pipeline to run (-p or --pipeline).")
    if not args.features:
        raise RuntimeError(
            "You must specify which features to use for clustering (-f or --features).")
    if not args.clusterees:
        raise RuntimeError(
            "You must specify which objects to cluster over (-l or --clusterees).")
    if not args.nclusters:
        args.nclusters = 4
    if not args.clusterer:
        args.clusterer = "spectral"
    if not args.outputfeatures:
        args.outputfeatures = "outputfeatures"
    if not args.outputclusters:
        args.outputclusters = "outputclusters"
    if not args.outputmouseovers:
        args.outputmouseovers = "outputmouseovers"

def run(source, pipeline, nclusters, featurecode,
        clusterees, clusterer,
        outputclusters, outputfeatures, outputmouseovers,
        inputfeatures, inputmouseovers,
        pcadims, normalize):

    logger.debug("[run] - Beginning execution.")
    logger.debug("[run] - Parameter: source = " + str(source))
    logger.debug("[run] - Parameter: pipeline = " + str(pipeline))
    logger.debug("[run] - Parameter: nclusters = " + str(nclusters))
    logger.debug("[run] - Parameter: featurecode = " + str(featurecode))
    logger.debug("[run] - Parameter: clusterees = " + str(clusterees))
    logger.debug("[run] - Parameter: clusterer = " + str(clusterer))
    logger.debug("[run] - Parameter: outputclusters = " + str(outputclusters))
    logger.debug("[run] - Parameter: outputfeatures = " + str(outputfeatures))
    logger.debug("[run] - Parameter: inputfeatures = " + str(inputfeatures))
    logger.debug("[run] - Parameter: pcadims = " + str(pcadims))
    logger.debug("[run] - Parameter: normalize = " + str(normalize))

    if (pipeline in NON_PCA_PIPELINES) and pcadims is not None:
        raise RuntimeWarning(
            "Incompatible option specified: PCA is not used with this pipeline.")
    if (pipeline in PCA_PIPELINES) and pcadims is None:
        raise RuntimeWarning(
            "You need to specify the number of dimensions to reduce to using PCA (using the -d flag).")

    if inputfeatures is None or inputmouseovers is None:
        data, mouseovers = fetch_data(source, clusterees)
        output_mouseovers(mouseovers, outputmouseovers)
        start = time()
        features = featurize(data, featurecode)
        output_features(features, outputfeatures)
    else:
        features = fetch_features(inputfeatures)
        mouseovers = fetch_mouseovers(inputmouseovers)

    points = [feature[1:] for feature in features]  # Exclude the object ID.
    ids = [feature[0] for feature in features] # The object IDs.
    if normalize:
        points = normalize_points(points)

    clusters, projected_points = run_pipeline(pipeline, nclusters, points, outputclusters, clusterer, pcadims)
    output_clusters(ids, clusters, outputclusters)
    plot(projected_points, clusters, outputclusters)
    output_visualization_data(projected_points, clusters, mouseovers, outputclusters)
    output_projected_points(ids, projected_points, features, outputclusters)


if __name__ == "__main__":
    args = get_args()
    check_args(args)
    source = queryutils.arguments.initialize_source(args.source, args)
    run(source, int(args.pipeline), args.nclusters, args.features,
        args.clusterees, args.clusterer,
        args.outputclusters, args.outputfeatures, args.outputmouseovers,
        args.inputfeatures, args.inputmouseovers,
        args.pcadimension, args.normalize)
