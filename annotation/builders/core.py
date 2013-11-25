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

    def finalize(self):
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

        log.debug("Couldn't find transform for {}".format(record))

    def post_transform(self, node, record):
        for handler in self.handlers:
            try:
                handler.post_transform(node, record)
            except NotImplementedError:
                pass

    def finalize(self):
        for handler in self.handlers:
            try:
                handler.finalize()
            except NotImplementedError:
                pass

    def build(self, records):
        # Go through every record and transform it into a node
        for record in records:
            node = self.transform(record)
            if node:
                self.post_transform(node, record)
                yield node

        self.finalize()


class AnnotationBuilder(object):
    Builder = Builder

    def __init__(self, Annotation):
        self.builder = self.Builder()
        self.Annotation = Annotation


class ParentNotFound(Exception):
    def __init__(self, parent_ID):
        self.parent_ID = parent_ID


class _LinkerIndex(MutableMapping):
    def __init__(self, *args, **kwargs):
        self.store = {}
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        try:
            return self.store[key]
        except KeyError:
            raise ParentNotFound(key)

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
        self._orphans = defaultdict(list)

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

        # Resolve any orphans that were looking for this parent record
        try:
            orphans = self._orphans.pop(ID)
        except KeyError:
            pass
        else:
            for node, record in orphans:
                self._link(node, record)

        try:
            self._link(node, record)
        except ParentNotFound as e:
            orphan = node, record
            self._orphans[e.parent_ID].append(orphan)

    def _resolve_orphans(self, orphans):
        for node, record in orphans:
            log.warning('Orphan: {}'.format(node))
