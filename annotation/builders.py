import logging
import re

import gff

log = logging.getLogger('annotation.builder')

def noop(*args, **kwargs): pass

class Handler(object):
    def __init__(self, matchers, transformer, post_transformer=noop):
        self.matchers = matchers
        self.transformer = transformer
        self.post_transformer = post_transformer


class HandlerNotFound(Exception): pass

class GFFBuilder(object):
    # TODO what if a record has multiple parents?

    def __init__(self, handlers):
        self.handlers = handlers

    def _find_handler(self, node):
        for handler in self.handlers:
            for matcher in handler.matchers:
                if callable(matcher) and matcher(node.record):
                    return handler
                elif re.match(matcher, node.record.type):
                    return handler

        raise HandlerNotFound()

    def transform_node(self, node, parent):
        try:
            handler = self._find_handler(node)
        except HandlerNotFound:
            log.debug("Couldn't find handler for {}".format(node))
        else:
            transformed = handler.transformer(node.record)
            transformed.parent = parent
            for child in node.children:
                self.transform_node(child, transformed)
            handler.post_transformer(transformed, node)

    # TODO is it weird to pass in the root like this? probably.

    def from_tree(self, gff_tree, root):
        print gff_tree.children
        for child in gff_tree.children:
            self.transform_node(child, root)

    def from_records(self, records, root):
        tree = gff.GFFTreeNode.from_records(records)
        return self.from_tree(tree, root)

    def from_file(self, path, root):
        with open(path) as fh:
            records = gff.GFF.from_stream(fh)
            return self.from_records(records, root)
