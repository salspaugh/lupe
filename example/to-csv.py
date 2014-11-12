import csv
import sys

input = sys.argv[1]
user = sys.argv[2]
output = "tmp"
with open(input) as input, open(output, "w") as output:
    writer = csv.writer(output)
    for line in input.readlines():
        line = line.strip()
        writer.writerow([user, line])
