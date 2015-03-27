import json
from BigStash import models


class ModelEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, models.ModelBase):
            return dict((k, getattr(obj, k)) for k in obj._slots)
        return super(ModelEncoder, self).default(obj)


def model_to_json(obj):
    return json.dumps(obj, cls=ModelEncoder)
