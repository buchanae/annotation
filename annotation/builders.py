from collections import defaultdict
import logging
import re

import gff

log = logging.getLogger('annotation.builder')

class MultipleParents(Exception): pass

class Handler(object):

    def __init__(self, types):
        self.types = types

    def matches(self, record):
        return record.type in self.types

    @staticmethod
    def transformer(record): pass

    @staticmethod
    def post_transformer(node, record): pass

    @staticmethod
    def ID(record):
        return record.ID

    @staticmethod
    def parent_ID(record):
        parent_IDs = record.parent_IDs

        if parent_IDs:
            if len(parent_IDs) == 1:
                return parent_IDs[0]
            elif len(parent_IDs) > 1:
                # Note: this library doesn't yet know how to handle multiple parents.
                #       We raise an exception to ensure the user knows that.
                # TODO error message
                # TODO consider logging an error or warning instead
                raise MultipleParents()


class HandlerNotFound(Exception): pass

class GFFBuilder(object):
    # TODO what if a record has multiple parents?

    def __init__(self, handlers):
        self.handlers = handlers

    def _find_handler(self, record):
        for handler in self.handlers:
            if handler.matches(record):
                return handler

        raise HandlerNotFound()

    # TODO is it weird to pass in the root like this? probably.

    def from_records(self, records, root):
        children_of = defaultdict(list)
        orphans = []

        # Go through every record and transform it into an annotation Model
        # e.g. gff record -> Gene instance
        for record in records:
            try:
                handler = self._find_handler(record)
            except HandlerNotFound:
                log.debug("Couldn't find handler for {}".format(record))
            else:
                node = handler.transformer(record)

                ID = handler.ID(record)
                parent_ID = handler.parent_ID(record)
                x = ID, node

                if parent_ID:
                    children_of[parent_ID].append(x)
                else:
                    orphans.append(x)

        # We make a second pass to link the nodes into a tree.
        # We make two passes because we can't guarantee that a parent is defined
        # before it's children (GFF files are frequently a mess).
        #
        # TODO consider requiring that parents are defined before children
        #      for the sake of efficiency, and provide an alternative to fix the GFF
        #      file, or a less efficient version

        def link_children(ID, node):
            for child_ID, child in children_of[ID]:
                child.parent = node
                link_children(child_ID, child)

        for ID, orphan in orphans:
            link_children(ID, orphan)
            orphan.parent = root
            

    def from_file(self, path, root):
        with open(path) as fh:
            records = gff.GFF.from_stream(fh)
            return self.from_records(records, root)
