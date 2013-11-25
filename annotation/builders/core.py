import logging


log = logging.getLogger('annotation.builder')


class Builder(object):

    def __init__(self, handlers=None):
        self.handlers = handlers or []

    def _inspect_handlers(self):
        all_hook_handlers = []
        hooks = ['transform', 'post_transform', 'finalize']

        for hook in hooks:
            hook_handlers = []
            all_hook_handlers.append(hook_handlers)

            for handler in self.handlers:
                func = getattr(handler, hook, None)
                if func:
                    hook_handlers.append(func)

        return all_hook_handlers

    def build(self, records):
        transforms, post_transforms, finalizes = self._inspect_handlers()

        # Go through every record and transform it into a node
        for record in records:
            for transform in transforms:
                node = transform(record)
                if node:
                    for post_transform in post_transforms:
                        post_transform(node, record)
                    yield node

        for finalize in finalizes:
            finalize()


# TODO AnnotationBuilder name conflicts with core.Builder since it's not a subclass
class AnnotationBuilder(object):
    Builder = Builder

    def __init__(self, Annotation):
        self.builder = self.Builder()
        self.Annotation = Annotation
