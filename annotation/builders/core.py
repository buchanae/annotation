import logging


log = logging.getLogger(__name__)


class Builder(object):

    def __init__(self):
        self.transform = []
        self.post_transform = []
        self.finalize = []

    def inspect_handler(self, handler):
        hooks = ['transform', 'post_transform', 'finalize']

        for hook in hooks:
            func = getattr(handler, hook, None)
            if func:
                getattr(self, hook).append(func)

    def iterbuild(self, records):
        # Go through every record and transform it into a node
        for record in records:
            for transform in self.transform:
                node = transform(record)
                if node:
                    for post_transform in self.post_transform:
                        post_transform(node, record)
                    yield node

        for finalize in self.finalize:
            finalize()

    def build(self, records):
        return list(self.iterbuild(records))
