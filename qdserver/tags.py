import yaml

from qdserver import ql
from qdserver.common import ID

from curry.typing import typeddict

TagInfo = typeddict(
    [ ('tagID', str)
    , ('tagName', str)
    , ('excludes', [ID])
    ], name='TagInfo')

TagEdge = typeddict(
    [ ('srcID', str)
    , ('dstIDs', [str])
    ], name='TagEdge')

class Tags(ql.QuerySpec):
    args_spec = [
        ('barID', ID),
    ]
    result_spec = [
        ('tagInfo', [TagInfo]),
        ('tagGraph', [TagEdge])
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        # TODO: Use args['barID']
        return allMenuTags

def register(dispatcher):
    dispatcher.register(Tags)

#=========================================================================#
# Tag Parsing
#=========================================================================#

def parse_tags(yaml_file):
    tags_yaml = yaml.load(yaml_file)
    groups = tags_yaml['tags']['groups']
    edges  = tags_yaml['tags']['edges']

    def resolve_tags(category):
        if category in categories:
            return categories[category]
        return ['#' + category] # category is a tag, e.g. 'beer'

    categories = {category: tags.split() for category, tags in groups.items()}
    tagGraph = []
    tagInfo  = []
    for category, children_str in edges.items():
        src_tags = resolve_tags(category)
        dst_tags = [ tag for child in children_str.split()
                             for tag in resolve_tags(child) ]
        for src_tag in src_tags:
            tagGraph.append(TagEdge(srcID=src_tag, dstIDs=dst_tags))

    for tags in categories.values():
        for tag in tags:
            excludes = list(tags)
            excludes.remove(tag)
            tagInfo.append(TagInfo(tagID=tag, tagName=tag, excludes=excludes))

    return Tags.make(tagInfo=tagInfo, tagGraph=tagGraph)

allMenuTags = parse_tags(open('Tags.yaml'))
