import yaml
import os
import json
from jsonschema import validate

from willitlink.base.graph import MultiGraph

from fixup_schema import is_new_schema, old_schema_to_new_schema, new_schema_to_old_schema

# This file should be the way to interact with all external files used and generated by this
# project.
#
# Current sources are (relative to the base directory passed into the functions below):
PROJECT_STRUCTURE_FILENAME = "modules.yaml" # human generated modules structure
WILLITLINK_DATA_DIRECTORY = "willitlink-data" # data generated by willitlink
PROCESSED_PROJECT_STRUCTURE_FILENAME = "modules_processed.yaml" # merged version of the two data sources above

MODULES_SCHEMA_FILE = "schema.yaml"
default_cwd = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
schema_file_name = os.path.join(default_cwd, MODULES_SCHEMA_FILE)

# Janky POC code to output yaml dictionaries as ordered dictionaries
# TODO: This works, but I should actually clean it up or figure out how it works...
# Source: http://pyyaml.org/ticket/29#comment:11 linked from
# http://stackoverflow.com/questions/8651095/controlling-yaml-serialization-order-in-python

import yaml
from yaml.representer import Representer
from yaml.constructor import Constructor, MappingNode, ConstructorError

def dump_anydict_as_map( anydict):
    yaml.add_representer( anydict, _represent_dictorder)
def _represent_dictorder( self, data):
    return self.represent_mapping('tag:yaml.org,2002:map', data.items() )

class Loader_map_as_anydict( object):
    'inherit + Loader'
    anydict = None      #override
    @classmethod        #and call this
    def load_map_as_anydict( klas):
        yaml.add_constructor( 'tag:yaml.org,2002:map', klas.construct_yaml_map)

    'copied from constructor.BaseConstructor, replacing {} with self.anydict()'
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, MappingNode):
            raise ConstructorError(None, None,
                    "expected a mapping node, but found %s" % node.id,
                    node.start_mark)
        mapping = self.anydict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:
                raise ConstructorError("while constructing a mapping", node.start_mark,
                        "found unacceptable key (%s)" % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

    def construct_yaml_map( self, node):
        data = self.anydict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

'''usage: 
   ...dictOrder = whatever-dict-thing

   class Loader( yaml_anydict.Loader_map_as_anydict, yaml.Loader):
       anydict = dictOrder
   Loader.load_map_as_anydict()
   yaml_anydict.dump_anydict_as_map( dictOrder)
   ...
   p = yaml.load( a, Loader= Loader)
'''

# This allows us to dump an OrderedDict with yaml.dump
from collections import OrderedDict
class OrderedDictLoader(Loader_map_as_anydict, yaml.Loader):
    anydict = OrderedDict
OrderedDictLoader.load_map_as_anydict()
dump_anydict_as_map(OrderedDict)

def read_yaml_file(filename):
    return yaml.load(open(filename), Loader=OrderedDictLoader)

def write_yaml_file(filename, output_dict):
    with open(filename, 'w') as f:
        f.write(yaml.dump(output_dict, indent=4, default_flow_style=False))



def validate_processed_project_structure_file_schema(project_data_directory):
    project_structure = read_yaml_file(os.path.join(project_data_directory, PROCESSED_PROJECT_STRUCTURE_FILENAME))
    project_schema = read_yaml_file(schema_file_name)
    return validate(project_structure, project_schema)

def validate_project_structure_file_schema(project_data_directory):
    project_structure = read_yaml_file(os.path.join(project_data_directory, PROJECT_STRUCTURE_FILENAME))
    project_schema = read_yaml_file(schema_file_name)
    return validate(project_structure, project_schema)



def read_project_structure_file(project_data_directory):
    project_structure_data = read_yaml_file(os.path.join(project_data_directory, PROJECT_STRUCTURE_FILENAME))
    if is_new_schema(project_structure_data):
        return project_structure_data
    else:
        return old_schema_to_new_schema(project_structure_data)

# TODO: Actually preserve the ordering as I dump the YAML file.  See
# http://stackoverflow.com/questions/8651095/controlling-yaml-serialization-order-in-python
def write_project_structure_file(project_data_directory, project_structure):
    write_yaml_file(os.path.join(project_data_directory, PROJECT_STRUCTURE_FILENAME), project_structure)



def read_processed_project_structure_file(project_data_directory):
    return read_yaml_file(os.path.join(project_data_directory, PROCESSED_PROJECT_STRUCTURE_FILENAME))

# TODO: Actually preserve the ordering as I dump the YAML file.  See
# http://stackoverflow.com/questions/8651095/controlling-yaml-serialization-order-in-python
def write_processed_project_structure_file(project_data_directory, project_structure):
    write_yaml_file(os.path.join(project_data_directory, PROCESSED_PROJECT_STRUCTURE_FILENAME), project_structure)



def get_willitlink_data_directory(project_data_directory):
    return os.path.join(project_data_directory, WILLITLINK_DATA_DIRECTORY)

def load_willitlink_graph(project_data_directory):
    return MultiGraph(timers=False).load(get_willitlink_data_directory(project_data_directory))
