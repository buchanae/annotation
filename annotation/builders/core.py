from __future__ import absolute_import

from collections import defaultdict
import logging
import re


log = logging.getLogger('annotation.builder')


class Handler(object):
    def transform(self, record):
        raise NotImplementedError()

    def post_transform(self, obj, record):
        raise NotImplementedError()

    def finalize(self, obj, record):
        raise NotImplementedError()


class Builder(object):

    def __init__(self, handlers=None):
        self.handlers = handlers or []

    def transform(self, record):
        for handler in self.handlers:
            try:
                node = handler.transform(record)
                if node:
                    return node
            except NotImplementedError:
                pass

        log.debug("Couldn't find handler for {}".format(record))

    def post_transform(self, node, record):
        for handler in self.handlers:
            try:
                handler.post_transform(node, record)
            except NotImplementedError:
                pass

    def finalize(self, node, record):
        for handler in self.handlers:
            try:
                handler.finalize(node, record)
            except NotImplementedError:
                pass

    def build(self, records):
        # Go through every record and transform it into a node
        for record in records:
            node = self.transform(record)
            if node:
                self.post_transform(node, record)
                yield node
        
    def build_and_finalize(self, records):
        nodes_records = []

        for node in self.iterbuild(records):
            nodes_records.append((node, record))

        for node, record in nodes_records:
            self.finalize(node, record)
            yield node


class ParentNotFound(Exception): pass


class Linker(Handler):
    def __init__(self):
        self.patterns = []
        self.parents_by_ID = {}
        self.orphans = []

    def add_pattern(self, parent_attr='parent', parent_ID_attr=None):
        if not parent_ID_attr:
            parent_ID_attr = parent_attr + '_ID'
        self.patterns.append((parent_attr, parent_ID_attr))

    def _link(self, node, record):
        for parent_attr, parent_ID_attr in self.patterns:
            parent_ID = getattr(node, parent_ID_attr, None)
            if parent_ID:
                try:
                    parent = self.parents_by_ID[parent_ID]
                except KeyError:
                    orphan = node, record
                    self.orphans.append(orphan)
                else:
                    setattr(node, parent_attr, parent)

    def _get_ID(self, node, record):
        return node.ID

    def post_transform(self, node, record):
        ID = self._get_ID(node, record)
        if ID:
            self.parents_by_ID[ID] = node

        self._link(node, record)

    def finalize(self):
        for node, record in self.orphans:
            try:
                self._link(node, record)
            except ParentNotFound:
                # TODO error message
                log.warning('Orphan')
