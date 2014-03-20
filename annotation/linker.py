from collections import defaultdict

# TODO ensure that handlers/builders/linkers always clean up after build


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
