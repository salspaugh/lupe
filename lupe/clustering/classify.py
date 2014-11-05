import csv
import numpy
import random

#from sklearn import tree # import sklearn does not work
from sklearn import ensemble 

TESTING_PROPORTION = .3

def read_training_data(filename):
    with open(filename, "r") as data:
        reader = csv.reader(data)
        rows = [r for r in reader][1:] # leave out header
        X = numpy.array([[float(f) for f in r] for r in rows])
        Y = numpy.array([int(r[0]) for r in rows])
        return X, Y

def divide_into_training_and_test(X, Y):
    test_X = []
    test_Y = []
    train_X = []
    train_Y = []
    for (x, y) in zip(X, Y):
        if random.uniform(0, 1) < TESTING_PROPORTION:
            test_X.append(x)
            test_Y.append(y)
        else:
            train_X.append(x)
            train_Y.append(y)
    return test_X, test_Y, train_X, train_Y

def fit_classifier(training_data):
    X, Y = read_training_data(training_data)
    test_X, test_Y, train_X, train_Y = divide_into_training_and_test(X, Y)
    #clf = tree.DecisionTreeClassifier()
    clf = ensemble.RandomForestClassifier()
    clf = clf.fit(train_X, train_Y)
    print "Classifier accuracy: %f" % clf.score(test_X, test_Y)
    return clf

def classify(data, clf):
    return clf.predict(data)
