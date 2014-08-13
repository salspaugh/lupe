import csv
import json

AGGREGATE_EXAMPLES = {
    "standard": [
        "127028.0",
        "168703.0",
        "196368.0",
        "131892.0",
        "89933.0",
        "11366.0",
        "189500.0",
        "145976.0",
        "145902.0",
        "146051.0"],
    "top": [
        "145023.0",
        "202446.0",
        "52750.0",
        "145628.0",
        "145630.0",
        "202418.0",
        "175647.0",
        "199326.0",
        "145755.0",
        "120343.0"],
    "by_time": [
        "162897.0",
        "123644.0",
        "202383.2"],
    "visualize": [
        "127302.0",
        "127041.0",
        "54865.0",
        "127304.0",
        "146223.0",
        "173541.0",
        "200590.0",
        "126292.0",
        "163371.0",
        "146016.0"],
    "visualize_time": [
        "127060.0",
        "123655.0",
        "94544.0",
        "146231.0",
        "130170.0",
        "127303.0",
        "4741.1",
        "80982.0",
        "176492.0",
        "49991.0"]
}

AUGMENT_EXAMPLES = {
    "arithmetic": [
        "57055.0",
        "11977.4",
        "202163.2",
        "171900.4",
        "32089.1",
        "32089.0",
        "124781.2",
        "145938.5",
        "148868.2",
        "168621.0"],
    "string_manipulation": [
        "119777.1",
        "127302.0",
        "36216.0",
        "37688.0",
        "110398.3",
        "202050.0",
        "202092.0",
        "202388.1",
        "177515.0",
        "177503.0",
        "74656.6",
        "202163.3",
        "39930.1",
        "171900.8"],
    "multivalue": [
        "119777.2",
        "156212.2",
        "202170.1",
        "175606.0",
        "175599.1",
        "202388.2",
        "170913.4"],
    "datetime_conversion": [
        "117306.0",
        "17656.0",
        "168621.1",
        "171900.3",
        "124848.0",
        "175838.0",
        "117306.0",
        "128648.2",
        "175597.0",
        "119777.5"],
    "complicated": [
        "200417.1",
        "30058.0"],
    "grouping": [
        "145938.1",
        "39772.8",
        "202163.0"],
    "conditionals": [
        "124840.0",
        "188921.0",
        "39772.4",
        "125894.0",
        "134859.1",
        "54901.2",
        "24840.0",
        "175603.1",
        "171900.6",
        "175602.4"],
    "field_value_assignments": [
        "196423.1",
        "146029.2",
        "89953.0",
        "32568.0",
        "37080.0",
        "196423.1",
        "74641.0",
        "196540.0",
        "119610.1",
        "175652.1"],
}

FILTER_EXAMPLES = {
    "subsearches": [
        "154311.0",
        "79441.0",
        "123751.0"],
    "function_based": [
        "146051.1",
        "184584.0",
        "12238.1",
        "175838.0",
        "146029.1",
        "125769.1",
        "172158.1",
        "171900.2",
        "163714.0",
        "171983.0"],
    "time_range_search": [
        "4390.0",
        "177964.0",
        "30058.0",
        "4345.0",
        "4419.0",
        "177737.0",
        "31462.0",
        "4428.0",
        "127377.0",
        "4741.0"],
    "selection": [
        "94570.0",
        "146387.0",
        "50086.0",
        "164727.0",
        "118597.0"],
    "simple_string_search": [
        "162787.0",
        "138758.0",
        "126973.0",
        "196525.1",
        "128260.0"],
    "field_value_search": [
        "163564.0",
        "79753.0",
        "144597.0",
        "74426.0",
        "199511.0",
        "82488.0",
        "202201.1",
        "202201.0",
        "40683.0"],
    "dedup": [
        "202163.1",
        "165345.1",
        "3801.1",
        "164802.1",
        "175652.1",
        "165345.1",
        "196540.1",
        "168621.1",
        "123845.1",
        "131418.1"],
    "macro": [
        "124777.0",
        "124703.0",
        "126165.0",
        "124779.0",
        "126241.0",
        "80857.0",
        "163745.0",
        "126087.0",
        "163734.0",
        "146143.0"],
    "logical": [
        "202564.0",
        "202689.0",
        "184636.1",
        "127015.0",
        "175610.0",
        "162179.0",
        "134653.0",
        "31420.0",
        "201338.0",
        "202439.0"],
    "index": [
        "165490.1",
    ],
    "regex": [
        "176466.1"
    ]
}

def write_examples(examples, all_features, output):
    examples = sorted(examples.iteritems())
    classes = { k:idx for idx, (k,v) in enumerate(examples) }
    
    classes_output = "%s-classes-codes.csv" % output
    with open(classes_output, "w") as classes_code:
        writer = csv.writer(classes_code)
        writer.writerow(["name", "code"])
        for (name, code) in classes.iteritems():
            writer.writerow([name, code])
    
    examples_output = "%s-training-data.csv" % output
    with open(examples_output, "w") as example_matrix:
        writer = csv.writer(example_matrix)
        has_header = False
        for (cls, instances) in examples:
            for i in instances:
                features = lookup_example(i, all_features)
                if features is not None:
                    x = [float(f) for f in features[1:]]
                    y = [classes[cls]]
                    if not has_header:
                        header = ["X%d"]*len(x) 
                        header = [s % i for i, s in enumerate(header)]
                        header = ["Y"] + header
                        writer.writerow(header)
                        has_header = True
                    writer.writerow(y + x)
       
def lookup_example(obj_id, feature_dict):
    for obj in feature_dict:
        if obj["id"] == obj_id:
            return obj["features"][1:]

def output_training_data(examples, features, output):
    with open(features) as f:
        feature_dict = json.load(f)
    write_examples(examples, feature_dict, output)

if __name__ == "__main__":
    output_training_data(FILTER_EXAMPLES, "results/filters.clusters.projected-points.json", "filter")
    output_training_data(AUGMENT_EXAMPLES, "results/augments.clusters.projected-points.json", "augment")
    output_training_data(AGGREGATE_EXAMPLES, "results/aggregates.clusters.projected-points.json", "aggregate")
