import sys

k = float(sys.argv[1])
n = ((1/k)*(1 - 1/k)) / ((0.05/1.96)**2)

print "Number of samples needed: %.2f" % n
