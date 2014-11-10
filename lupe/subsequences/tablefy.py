import sys
import csv

with open(sys.argv[1]) as data:
    reader = csv.reader(data)
    base = "%d    & %d    & %.2f  & %s \\\\"
    for row in reader:
        len = int(row[0])
        cnt = int(float(row[1]))
        pct = float(row[2])
        seq = row[3].split()
        seq = ["textbf{%s}" % s for s in seq]
        seq = " | ".join(seq)
        line = base % (len, cnt, pct, seq)
        print line
