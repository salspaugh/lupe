#! /usr/bin/env python
"""
Python wrapper to execute c++ tSNE implementation
for more information on tSNE, go to :
http://ticc.uvt.nl/~lvdrmaaten/Laurens_van_der_Maaten/t-SNE.html

HOW TO USE
Just call the method calc_tsne(dataMatrix)

Created by Philippe Hamel
hamelphi@iro.umontreal.ca
October 24th 2008
"""
import sys
import os
import pylab
import numpy
import csv
import argparse

from os import getcwd, path
from numpy import linalg, cov, argsort, dot, empty, zeros
from struct import pack, unpack, calcsize


def calc_tsne(data_matrix, no_dims=2, perplexity=30, landmarks=1):
    """
    This is the main function.
    dataMatrix is a 2D numpy array containing your data (each row is a data point)
    Remark : landmarks is a ratio (0<landmarks<=1)
    If landmarks == 1 , it returns the list of points in the same order as the input
    """

    write_dat(data_matrix, no_dims, perplexity, landmarks)
    tSNE()
    xmat, lm, costs = read_result()
    clear_data()
    if landmarks == 1:
        x = re_order(xmat, lm)
        return x
    return xmat, lm


def readbin(type, file):
    """
    used to read binary data from a file
    """
    return unpack(type, file.read(calcsize(type)))


def write_dat(data_matrix, no_dims, perplexity, landmarks):
    """
    Generates data.dat
    """
    print 'Writing data.dat'
    print 'Dimension of projection : %i \nPerplexity : %i \nLandmarks(ratio) : %f' % (no_dims, perplexity, landmarks)
    n, d = data_matrix.shape
    f = open('data.dat', 'wb')
    f.write(pack('=iiid', n, d, no_dims, perplexity))
    f.write(pack('=d', landmarks))
    for inst in data_matrix:
        for el in inst:
            f.write(pack('=d', el))
    f.close()


def tSNE():
    """
    Calls the tsne c++ implementation depending on the platform
    """
    platform = sys.platform
    print'Platform detected : %s' % platform
    if platform in ['mac', 'darwin']:
        cmd = 'tSNE_maci'
    else:
        raise RuntimeError('You are not in right platform.')
    print 'Calling executable "%s"' % cmd
    cmd = path.join(path.dirname(__file__), cmd)
    os.system(cmd)


def read_result():
    """
    Reads result from result.dat
    """
    print 'Reading result.dat'
    f = open('result.dat', 'rb')
    n, nd = readbin('ii', f)
    xmat = empty((n, nd))
    for i in range(n):
        for j in range(nd):
            xmat[i, j] = readbin('d', f)[0]
    lm = readbin('%ii' % n, f)
    costs = readbin('%id' % n, f)
    f.close()
    return (xmat, lm, costs)


def re_order(xmat, lm):
    """
    Re-order the data in the original order
    Call only if landmarks==1
    """
    print 'Reordering results'
    x = zeros(xmat.shape)
    for i, lm in enumerate(lm):
        x[lm] = xmat[i]
    return x


def clear_data():
    """
    Clears files data.dat and result.dat
    """
    print 'Clearing data.dat and result.dat'
    os.system('rm data.dat')
    os.system('rm result.dat')

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input', help="input data points")
    ap.add_argument('-r', '--resultpngname',
                    help="name for output picture of data points after tsne")
    ap.add_argument('-c', '--xycoordinate',
                    help="name for output coordinate of data points after tsne")
    ap.add_argument('-p', '--perplexity', type=int, help="perplexity of tsne")
    args = ap.parse_args()
    points = args.input
    result = args.resultpngname
    output = args.xycoordinate
    p = args.perplexity

    x = Math.loadtxt(points, skiprows=1,
                     usecols=(2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12))
    labels = numpy.loadtxt(points, skiprows=1, usecols=[1])
    y = calc_tsne(x, no_dims=2, perplexity=p, landmarks=1)
    writer = csv.writer(open(output, "wb"))
    writer.writerows(y)

    pylab.scatter(y[:, 0], y[:, 1], 20, labels)
    pylab.savefig(result)
