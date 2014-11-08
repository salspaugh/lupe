import searches01
import filters01
import aggregates01
import augments01
import querygroups01

FEATURES =  searches01.FEATURES + \
            filters01.FEATURES + \
            aggregates01.FEATURES + \
            augments01.FEATURES + \
            querygroups01.FEATURES

try:
    import sessions01
    FEATURES += sessions01.FEATURES
except Exception as e:
    print e
try:
    import sessions02
    FEATURES += sessions02.FEATURES
except Exception as e:
    print e
try:
    import sessions03
    FEATURES += sessions03.FEATURES
except Exception as e:
    print e
