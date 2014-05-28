from features import FEATURES
from traceback import print_exc

def get_features(desired_versions):
    features = []
    for f in FEATURES:
        for v in f.versions:
            if v in desired_versions:
                features.append(f)
    return features

def featurize_obj(obj, features):
    featvec = []
    for feature in features:
        try: 
            f = feature.check(obj)
            if type(f) == type([]):
                featvec += [float(x) for x in f]
            else:
                featvec.append(float(f))
        except Exception as error:
            print_exc()
            return None
    return featvec 
