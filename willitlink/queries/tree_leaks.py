from willitlink.base.graph import MultiGraph
from willitlink.base.dev_tools import Timer
from willitlink.queries.symbol_diff import get_symbol_info

def find_direct_leaks(graph, archive_names):

    # Get all symbols needed by this archive
    symbols_needed = get_symbol_info(graph,
                                     archive_names,
                                     search_depth=1,
                                     symbol_type='dependency')

    # Get all symbols provided by this archive and archives listed as dependencies
    symbols_found = set([ s['symbol']
                          for s in get_symbol_info(graph,
                                                   archive_names,
                                                   search_depth=None,
                                                   symbol_type='definition') ])


    leaks = []
    for symbol_needed in symbols_needed:
        if symbol_needed['symbol'] not in symbols_found:
            leaks.append(symbol_needed)

    o = []
    for leak_object in leaks:
        try:
            num_deps = len(graph.get('symbol_to_file_sources', leak_object['symbol']))

            if num_deps > 0:
                o.append(leak_object)
        except KeyError:
            pass

    return o
