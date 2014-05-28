
import spectral as spectral_module
import kmedoids as kmedoids_module
from featurize import get_features

from argparse import ArgumentParser
from numpy import array, linalg, zeros

# TODO: Add clustering methods from scipy here.

def kmedoids(points, k):
    distances = build_distance_matrix(points)
    return kmedoids_module.cluster(distances, k=k)

def spectral(points, k):
    distances = build_distance_matrix(points)
    return spectral_module.cluster(distances, k=k)

def build_distance_matrix(data, normalize=False):
    m = len(data)
    distances = zeros((m, m))
    i = j = 0.
    max_distance = -1e10
    for i in range(m):
        for j in range(i + 1, m):
            p = data[i]
            q = data[j]
            distance = dist(p, q)
            max_distance = max(max_distance, distance)
            distances[i, j] = distances[j, i] = distance
    if normalize:
        return distances / max_distance
    return distances

def dist(a, b):
    a = array([float(x) for x in a])
    b = array([float(x) for x in b])
    return linalg.norm(a - b)

def main(k, input, output):
    points, ids = read_points(input)
    clusters, centers = spectral(points, k=k)
    feature_names = [f.__name__ for f in get_features()]
    header = ["session_id", "cluster_id"] + feature_names
    with open(output, 'w') as results:
        writer = csv.writer(results)
        writer.writerow(header)
        for id, cluster, point in zip(ids, clusters, points):
            line = [id, cluster] + points
            writer.writerow(line)

def read_points(filename):
    with open(filename, 'r') as csvfile:
        points = []
        ids = []
        reader = csv.reader(csvfile)
        for row in reader:
            ids.append(int(row.pop()))
            points.append(row)
    return points, ids

if __name__ == "__main__":
    parser = ArgumentParser()
    # TODO: Write help message for these.
    parser.add_argument("-i", "--input")
    parser.add_argument("-o", "--output")
    parser.add_argument("-k", "--nclusters")
    args = parser.parse_args()
    main(args.nclusters, args.input, args.output)

