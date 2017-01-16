from os.path import dirname, abspath, join

import yaml
import uuid
from curry import fmap, chunking
from curry.typing import alias, typeddict, URL

from qdserver import model

root = dirname(abspath(__file__))

fresh_id = uuid.uuid4

ItemID = alias('ItemID', str)
TagName = alias('TagName', str)

Drink = typeddict(
    [ ('name',  str)
    , ('desc',  str)
    , ('image', URL)
    , ('abv',   str)
    , ('tags',  str)
    ], name='Drink')

Drinks = { ItemID: Drink }

Contents = typeddict(
    [ ('drinks', Drinks)
    ], name='Contents')

def tag_to_tag_id(tag_name):
    return tag_name

def prepare_item(item_name, item):
    images = []
    if item.get('image') or item.get('images'):
        images = item.get('image') or item.get('images')
        images = fmap(str.strip, images.split())

    if 'name' not in item:
        raise ValueError("'name' field is missing", item)
    # if 'desc' not in item:
    #     raise ValueError("'desc' field is missing", item)
    if 'tags' not in item:
        raise ValueError("'tags' field is missing", item)

    return {
        'id':       item_name,
        'name':     item['name'],
        'desc':     item.get('desc', None),
        'images':   images,
        'tags':     fmap(tag_to_tag_id, filter(bool, item['tags'].split())),
    }

def load_items_from_file(contents, dry_run=False):
    drink_list = contents['drinks']
    results = [prepare_item(item_name, item)
                   for item_name, item in drink_list.items()]
    if not dry_run:
        model.run(model.MenuItemDefs.delete())
        model.run(model.MenuItemDefs.insert(results))

if __name__ == '__main__':
    yaml_file = yaml.load(open(join(root, 'drinks.yaml')))
    load_items_from_file(yaml_file, dry_run=False)
