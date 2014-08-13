import csv
import numpy

from sklearn import tree # import sklearn does not work

def read_training_data(filename):
    with open(filename, "r") as data:
        reader = csv.reader(data)
        rows = [r for r in reader][1:] # leave out header
        X = numpy.array([[float(f) for f in r] for r in rows])
        Y = numpy.array([int(r[0]) for r in rows])
        return X, Y

def fit_classifier(training_data):
    X, Y = read_training_data(training_data)
    clf = tree.DecisionTreeClassifier()
    clf = clf.fit(X, Y)
    return clf

def classify(data, clf):
    return clf.predict(data)
