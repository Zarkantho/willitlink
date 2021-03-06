def generate_file_graph(g):
    object_files = [ i for i in g.files if i.endswith(".o") ]

    file_graph_hash = {}
    for object_file in object_files:
        file_graph_hash[object_file] = {}
        if 'client_build' in object_file:
            continue
        for symbol_needed in g.get('file_to_symbol_dependencies', object_file):
            for file_providing_symbol in g.get('symbol_to_file_sources', symbol_needed):
                if 'client_build' in file_providing_symbol:
                    continue
                if file_providing_symbol not in file_graph_hash[object_file]:
                    file_graph_hash[object_file][file_providing_symbol] = []
                file_graph_hash[object_file][file_providing_symbol].append(symbol_needed)

    return file_graph_hash
