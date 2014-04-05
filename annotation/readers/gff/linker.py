from annotation.build import Linker as LinkerBase


class Linker(LinkerBase):

    def __init__(self, parent_type, child_type, link_fn,
                 parent_key=None):

        super(Linker, self).__init__()
        self.parent_type = parent_type
        self.child_type = child_type
        self.link_fn = link_fn
        self.parent_key = parent_key

    def post_transform(self, node, record):
        if isinstance(node, self.parent_type):
            self.parents[node.ID] = node

        elif isinstance(node, self.child_type):
            if self.parent_ID_func:
                parent_ID = self.parent_ID_func(node, record)
            else:
                parent_ID = record.parent_ID

            self.children[parent_ID].append(node)
