from flask.json import JSONEncoder
from database_setup import *


class CatalogJSONEncoder(JSONEncoder):
    """Serializes catalog data into dictionary objects suitable for use with
    Python's "json" module.

    Args:
        obj: Root object where serialization should begin.

    Returns:
        Dictionary containing information to be serialized to JSON.
    """

    def default(self, obj):
        if isinstance(obj, Category):
            return {
                'id': obj.id,
                'name': obj.name,
                'items': CatalogJSONEncoder.default(self, obj.items)
            }

        elif all([isinstance(c, CatalogItem) for c in obj]):
            return [{'id': item.id,
                     'name': item.name,
                     'description': item.description}
                    for item in obj]

        return super(CatalogJSONEncoder, self).default(obj)
