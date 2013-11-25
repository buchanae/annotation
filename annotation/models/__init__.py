from __future__ import absolute_import

from annotation.models import bases, sequences


__version__ = '2.0.0'

# TODO drop strand and use a boolean "reversed" or "reverse_strand" instead?


class TreeNode(object):
    '''Dead simple representation of a tree node.

    A tree node has one parent and multiple children.

    When a TreeNode's parent is set, the child is added to the parent's
    children automatically, and likewise if the parent is unset,
    the child is removed from the parent's children.

    Note, this does not (yet) handle the opposite, i.e. if you remove
    a child node from the parent, that child's parent is not unset.
    '''
    def __init__(self):
        self._parent = None
        self.children = []

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        # If this node already has a parent,
        # delete this node from that parent's children
        if self._parent:
            self._parent.children.remove(self)
        self._parent = value
        self._parent.children.append(self)


class Parent(object):
    def __init__(self, Parent_cls, name=None, related_name=None):
        self._name = name
        self.Parent_cls = Parent_cls
        self.related_name = related_name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        if not self.related_name:
            self.related_name = name + '_set'

    def __get__(self, obj, cls=None):
        return obj._model_data.get(self.name)

    def __set__(self, obj, new_parent):
        current_parent = self.__get__(obj)
        if current_parent:
            related_set = getattr(current_parent, self.related_name)
            related_set.remove(obj)

        obj._model_data[self.name] = new_parent

        if new_parent:
            # TODO catch missing related attr on parent?
            related_set = getattr(new_parent, self.related_name)
            related_set.add(obj)


class ModelMeta(type):
    def __init__(cls, name, bases, attrs):
        for key, value in attrs.items():
            if isinstance(value, Parent):
                value.name = key
        super(ModelMeta, cls).__init__(name, bases, attrs)


class Model(object):
    __metaclass__ = ModelMeta

    def __init__(self, *args, **kwargs):
        self._model_data = {}
        super(Model, self).__init__(*args, **kwargs)


class Annotation(Model):
    # TODO move to bases
    def __init__(self):
        self.references = set()


class Reference(Model, bases.Reference, sequences.ReferenceSequencesMixin):

    annotation = Parent(Annotation, related_name='references')

    @classmethod
    def from_GFF(cls, record):
        return cls(record.ID, record.end)


class Gene(Model, bases.Gene):

    reference = Parent(Reference, related_name='genes')

    @classmethod
    def from_GFF(cls, record):
        return cls(record.ID, record.strand)

    def GFF_reference_ID(self, record):
        return record.parent_ID or record.seqid


class Transcript(Model, bases.Transcript, sequences.TranscriptSequencesMixin):

    gene = Parent(Gene, related_name='transcripts')

    @classmethod
    def from_GFF(cls, record):
        return cls(record.ID)

    @property
    def reference(self):
        return self.gene.reference


class Exon(Model, bases.Exon):

    transcript = Parent(Transcript, related_name='exons')

    @classmethod
    def from_GFF(cls, record):
        return cls(record.start, record.end)

    @property
    def reference(self):
        return self.transcript.gene.reference
