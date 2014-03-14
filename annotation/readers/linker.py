from collections import defaultdict, MutableMapping


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


# TODO ugh, this whole pattern is too confusing
class Linker(object):

    _ParentIndex = _LinkerIndex

    def __init__(self):
        self._index = self._ParentIndex()
        self._orphans = defaultdict(list)

    def _get_ID(self, node, record):
        raise NotImplementedError()

    def _get_parent_ID(self, node, record):
        raise NotImplementedError()

    def _link(self, child, parent):
        raise NotImplementedError()

    def _try_link(self, node, record):
        parent_ID = self._get_parent_ID(node, record)
        if parent_ID:
            parent = self._index[parent_ID]
            self._link(node, parent)

    def _resolve_orphans(self, ID, node):
        # Resolve any orphans that were looking for this parent record
        try:
            orphans = self._orphans.pop(ID)
        except KeyError:
            pass
        else:
            for orphan_node, orphan_record in orphans:
                self._link(orphan_node, node)

    def _index_parent(self, node, record):
        ID = self._get_ID(node, record)
        if ID:
            self._index[ID] = node

        self._resolve_orphans(ID, node)

    def post_transform(self, node, record):
        self._index_parent(node, record)

        try:
            self._try_link(node, record)
        except ParentNotFound as e:
            orphan = node, record
            self._orphans[e.parent_ID].append(orphan)

    def finalize(self):
        for ID, orphans in self._orphans.items():
            for node, record in orphans:
                log.warning('Orphan: {}'.format(node))


class DumbLinker(Linker):

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

    def _link(self, child, parent):
        child.parent = parent
