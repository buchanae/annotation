from __future__ import absolute_import

from collections import defaultdict, MutableMapping
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


class AnnotationBuilder(object):
    Builder = Builder

    def __init__(self, Annotation):
        self.builder = self.Builder()
        self.Annotation = Annotation


class ParentNotFound(Exception): pass


class _LinkerIndex(MutableMapping):
    def __init__(self, *args, **kwargs):
        self.store = {}
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        try:
            return self.store[key]
        except KeyError:
            raise ParentNotFound()

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)


class Linker(Handler):

    _ParentIndex = _LinkerIndex

    def __init__(self):
        self._index = self._ParentIndex()
        self._orphans = []

    def _get_ID(self, node, record):
        try:
            return node.ID
        except AttributeError:
            pass

    def _get_parent_ID(self, node, record):
        try:
            return node.parent_ID
        except AttributeError:
            pass

    def _link(self, node, record):
        parent_ID = self._get_parent_ID(node, record)
        if parent_ID:
            parent = self._index[parent_ID]
            node.parent = parent

    def post_transform(self, node, record):
        ID = self._get_ID(node, record)
        if ID:
            self._index[ID] = node

        try:
            self._link(node, record)
        except ParentNotFound:
            orphan = node, record
            self._orphans.append(orphan)

    def finalize(self):
        for node, record in self._orphans:
            try:
                self._link(node, record)
            except ParentNotFound:
                # TODO error message
                log.warning('Orphan')
