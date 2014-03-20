from annotation.linker import Linker as LinkerBase


class Linker(LinkerBase):

    def __init__(self, parent_type, child_type, parent_attr,
                 parent_ID_func=None):

        super(Linker, self).__init__()
        self.parent_type = parent_type
        self.child_type = child_type
        self.parent_attr = parent_attr
        self.parent_ID_func = parent_ID_func

    def link(self, child, parent):
        setattr(child, self.parent_attr, parent)

    def post_transform(self, node, record):
        if isinstance(node, self.parent_type):
            self.parents[node.ID] = node

        elif isinstance(node, self.child_type):
            if self.parent_ID_func:
                parent_ID = self.parent_ID_func(node, record)
            else:
                parent_ID = record.parent_ID

            self.children[parent_ID].append(node)
