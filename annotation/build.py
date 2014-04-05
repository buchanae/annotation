from collections import defaultdict
import logging
import types


log = logging.getLogger(__name__)


class BuildError(Exception): pass


class Builder(object):

    def __init__(self):
        self.transform = []
        self.post_transform = []
        self.finalize = []

    def add_handler(self, handler):
        hooks = ['transform', 'post_transform', 'finalize']

        for hook in hooks:
            func = getattr(handler, hook, None)
            if func:
                getattr(self, hook).append(func)

    def iterbuild(self, records):
        # Go through every record and transform it into a node
        for record in records:
            for transform in self.transform:
                # Transformers should always use "yield", making them
                # generators, which allows transformers to yield multiple
                # nodes if they need to, e.g. to transform a single
                # CodingSequence object into multiple GFF records.
                result_gen = transform(record)

                if result_gen is None:
                    continue

                # Hopefully this prevents people from making the mistake
                # of using "return" when they should be using "yield".
                if not isinstance(result_gen, types.GeneratorType):
                    _msg = 'Tranform functions must be generators. Use "yield" instead of "return"'
                    raise BuildError(_msg)

                for node in result_gen:
                    for post_transform in self.post_transform:
                        post_transform(node, record)

                    # TODO check that node is not None?
                    yield node

        for finalize in self.finalize:
            finalize()

    def build(self, records):
        return list(self.iterbuild(records))


class Linker(object):

    def __init__(self):
        self.parents = {}
        self.children = defaultdict(list)

    def link(self, child, parent):
        child.parent = parent

    def post_transform(self, node, record):
        self.parents[node.ID] = node
        self.children[record.parent_ID].append(node)

    def finalize(self):
        for parent_ID, children in self.children.items():
            try:
                parent = self.parents[parent_ID]
            except KeyError:
                msg_tpl = 'Parent not found for {}'
                for child in children:
                    log.warning(msg_tpl.format(child))
            else:
                for child in children:
                    self.link(child, parent)
