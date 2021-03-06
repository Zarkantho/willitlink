from willitlink.cli.tools import get_graph, render

from willitlink.base.graph import MultiGraph
from willitlink.base.dev_tools import Timer

from willitlink.queries.family_tree import symbol_family_tree, file_family_tree

def get_tree_types():
    return {
        'symbol': get_symbol_family_tree,
        'file': get_file_family_tree,
    }

def get_tree(args):
    g = get_graph(args)

    for tree_type in get_tree_types().keys():
        if getattr(args, tree_type) is not None:
            tree = tree_type
            args.name = getattr(args, tree)
            break

    if tree is None:
        raise Exception('invalid tree type.')

    args.g = g
    get_tree_types()[tree](args)

def get_file_family_tree(args):
    if args.g is None:
        g = get_graph(args)
    else:
        g = args.g

    with Timer('get file family tree query', args.timers):
        render(file_family_tree(g, args.name, args.depth))


def get_symbol_family_tree(args):
    if args.g is None:
        g = get_graph(args)
    else:
        g = args.g

    if len(args.name) > 0:
        raise Exception('Currently only one symbol is allowed')

    with Timer('get symbol family tree query', args.timers):
        render(symbol_family_tree(g, args.name[0], args.depth))
