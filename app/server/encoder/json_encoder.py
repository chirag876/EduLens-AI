import json
from datetime import date, datetime

# from pandas import DataFrame as df


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        # if isinstance(o, np.integer):
        #     return int(o)
        # elif isinstance(o, np.floating):
        #     return float(o)
        # if isinstance(o, np.ndarray):
        #     return o.tolist()
        # if isinstance(o, df):
        #     return o.to_json(orient='table')
        return o.isoformat() if isinstance(o, (date, datetime)) else super().default(o)


def json_decoder(obj):
    if '__type__' in obj and obj['__type__'] == '__datetime__':
        return datetime.fromtimestamp(obj['epoch'])
    return obj


# Encoder function


def json_dumps(obj):
    return json.dumps(obj, cls=JSONEncoder)


# Decoder function


def json_loads(obj):
    return json.loads(obj, object_hook=json_decoder)


def serialize(obj):
    return json_loads(json_dumps(obj))
