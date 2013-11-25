import logging


log = logging.getLogger('annotation.builder')


class Builder(object):

    def __init__(self, handlers=None):
        self.handlers = handlers or []

    def _invoke(self, handler, name, *args, **kwargs):
        func = getattr(handler, name, None)
        if func:
            return func(*args, **kwargs)
        
    def transform(self, record):
        for handler in self.handlers:
            node = self._invoke(handler, 'transform', record)
            if node:
                return node

        log.debug("Couldn't find transform for {}".format(record))

    def post_transform(self, node, record):
        for handler in self.handlers:
            self._invoke(handler, 'post_transform', node, record)

    def finalize(self):
        for handler in self.handlers:
            self._invoke(handler, 'finalize')

    def build(self, records):
        # Go through every record and transform it into a node
        for record in records:
            node = self.transform(record)
            if node:
                self.post_transform(node, record)
                yield node

        self.finalize()


# TODO AnnotationBuilder name conflicts with core.Builder since it's not a subclass
class AnnotationBuilder(object):
    Builder = Builder

    def __init__(self, Annotation):
        self.builder = self.Builder()
        self.Annotation = Annotation
