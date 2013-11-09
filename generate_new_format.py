#!/usr/bin/env python

import re
import json
import pymongo
import subprocess
import sys
import dep_graph

# Strucutre of new format
# {
#    "symbols" : [
#        "mongo::inShutdown()",
#        ...
#    ],
#    "files" : [
#        "src/mongo/db/shutdown.o",
#        ...
#    ],
#    "symbol_sources" : { // symbol_to_file_sources
#         "mongo::inShutdown()" : [
#             "shutdown.o",
#         ],
#         ...
#    }
#    "symbol_dependents" : {  // symbol_to_file_dependencies
#         "mongo::inShutdown()" : [
#             "file_that_uses_shutdown.o",
#         ],
#         ...
#    }
#    "symbols_provided" : { // file_to_symbol_definitions
#         "shutdown.o" : [
#             "mongo::inShutdown()",
#         ],
#         ...
#    }
#    "symbols_needed" : { // file_to_symbol_dependencies
#         "file_that_uses_shutdown.o" : [
#             "mongo::inShutdown()",
#         ],
#         ...
#    }
#    "children" : { // target_to_dependencies
#         "libshutdown.a" : [
#             "libstringutils.a",
#         ],
#         "all" : [
#             "alltools",
#         ],
#         ...
#    }
#    "members" : { // archives_to_components
#         "libshutdown.a" : [
#             "shutdown.o",
#         ],
#         ...
#    }
#    "parents" : { // dependency_to_targets
#         "shutdown.o" : [
#             "libshutdown.a",
#         ],
#         "libstringutils.a" : [
#             "libshutdown.a"
#         ],
#         ...
#    }
# }

def generate_edges(build_objects):
    relationships = [
                      'symbol_to_file_sources', 'symbol_to_file_sources',
                      'file_to_symbol_definitions', 'file_to_symbol_dependencies',
                      'target_to_dependencies', 'archives_to_components', 'dependency_to_targets'
                    ]

    g = dep_graph.MultiGraph(relationships)
    g.make_lists(['symbols', 'files'])

    # Track how many nodes we've processed so far
    count = 0

    for build_object in build_objects:
        count += 1

        build_object_name = build_object['_id']

        # Add this file
        g.files.append(build_object_name)

        # Add the symbol dependency information for this file
        if build_object['type'] == 'object':

            # Iterate the symbol dependencies of this object, if applicable
            if 'symdeps' in build_object:
                for symdep in build_object['symdeps']:

                    # Skip this symbol if it's the empty string
                    if symdep == "":
                        continue

                    # Add this symbol to the set of all symbols
                    g.symbols.append(symdep)

                    # Add an edge to indicate that a file depends on these symbols
                    g.add(relationship='file_to_symbol_dependencies',
                          item=build_object_name,
                          deps=symdep)

                    # Add an edge to indicate that this symbol is needed by this file
                    g.add(relationship='symbol_to_file_dependencies',
                          item=symdep,
                          deps=build_object_name)

            if 'symdefs' in build_object:
                for symdef in build_object['symdefs']:

                    # Skip this symbol if it's the empty string
                    if symdef == "":
                        continue

                    # Add this symbol to the set of all symbols
                    g.symbols.append(symdef)

                    # Add an edge to indicate that this file provides this symbol
                    g.add(relationship='file_to_symbol_definitions',
                          item=build_object_name,
                          deps=symdef)

                    # Add an edge to indicate that this symbol is provided by this file
                    g.add(relationship='symbol_to_file_sources',
                          item=symdef,
                          deps=build_object_name)

        # Add the file dependency information for this file
        else:
            # Iterate the library dependencies of this build object, if applicable
            if 'deps' in build_object:
                for libdep in build_object['deps']:

                    # Add this symbol to the set of all files
                    g.files.append(libdep)

                    # Add an edge to indicate that this file provides this symbol
                    g.add(relationship='target_to_dependencies',
                          item=build_object_name,
                          deps=libdep)

                    # Add an edge to indicate that this symbol is provided by this file
                    g.add(relationship='dependency_to_targets',
                          item=libdep,
                          deps=build_object_name)

            # TODO: I believe we want to distinguish between objects and archives, but this treats
            # them all the same.
            # Iterate the object dependencies of this build object, if applicable
            if 'objects' in build_object:
                for objdep in build_object['objects']:

                    # Add this symbol to the set of all files
                    g.files.append(objdep)

                    # Add an edge to indicate that this file provides this symbol
                    g.add(relationship='archives_to_components',
                          item=build_object_name,
                          deps=objdep)

                    # Add an edge to indicate that this symbol is provided by this file
                    g.add(relationship='dependency_to_targets',
                          item=objdep,
                          deps=build_object_name)

        print(count)

    g.uniquify_lists()

    return g

def main():
    client = pymongo.MongoClient()

    try:
        out_fn = sys.argv[1]
    except IndexError:
        out_fn = 'new_format_deps.json'

    graph = generate_edges(client['test'].deps.find())

    graph.export(out_fn)

if __name__ == '__main__':
    main()
