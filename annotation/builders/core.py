from __future__ import absolute_import

from collections import defaultdict
import logging
import re


log = logging.getLogger('annotation.builder')


class HandlerNotFound(Exception): pass


# TODO idea: what if handlers could somehow communicate with one another?
#            could be very powerful.


class HandlerBase(object):

    def __init__(self, types):
        self.types = types

    def matches(self, record):
        return record.type in self.types

    def transform(self, record): pass

    # TODO post transform is not implemented in the builder
    def post_transform(self, node, record): pass

    def ID(self, record):
        return record.ID

    def parent_ID(self, record):
        return record.parent_ID

    @classmethod
    def make(cls, name, transform, post_transform=None):
        # transform and post_transform need to be wrapped so that they
        # accept the "self" argument, since they will be bound to a Handler instance
        # when they're created.
        def wrap(fn):
            def wrapper(self, *args, **kwargs):
                return fn(*args, **kwargs)
            return wrapper

        attrs = {'transform': wrap(transform)}

        if post_transform:
            attrs['post_transform'] = wrap(post_transform)

        return type(name, (cls,), attrs)


class Builder(object):

    def __init__(self, handlers):
        self.handlers = handlers

    def _find_handler(self, record):
        for handler in self.handlers:
            if handler.matches(record):
                return handler

        raise HandlerNotFound()

    def build(self, records, root=None):
        children_of = defaultdict(list)
        orphans = []

        # Go through every record and transform it into a node
        for record in records:
            try:
                handler = self._find_handler(record)
            except HandlerNotFound:
                log.debug("Couldn't find handler for {}".format(record))
            else:
                node = handler.transform(record)

                ID = handler.ID(record)
                parent_ID = handler.parent_ID(record)
                x = ID, node

                if parent_ID:
                    children_of[parent_ID].append(x)
                else:
                    orphans.append(x)

        # We make a second pass to link the nodes into a tree.
        # We make two passes because we can't guarantee that a parent is defined
        # before it's children (e.g. GFF files are frequently a mess).
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
            if root:
                orphan.parent = root

        if root:
            return root
        else:
            return orphans
