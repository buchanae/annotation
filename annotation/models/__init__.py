"""
Contains linked models.
For example:
- Gene is linked to Reference by the Parent relationship.
- Transcript has a sequence that depends on its exons and
  its reference's sequence.
"""
from __future__ import absolute_import

from annotation.models import bases, sequences
from annotation.models.relationships import Parent


class Region(bases.Region): pass


class ModelMeta(type):
    def __init__(cls, name, bases, attrs):
        for key, value in attrs.items():
            if isinstance(value, Parent):
                value.name = key
        super(ModelMeta, cls).__init__(name, bases, attrs)


class Model(object):
    __metaclass__ = ModelMeta

    # TODO use __new__?
    #      even need Model? Is there a better way to implement Parent?
    def __init__(self, *args, **kwargs):
        self._model_data = {}
        super(Model, self).__init__(*args, **kwargs)


class Annotation(Model, bases.Annotation):
    def __init__(self):
        super(Annotation, self).__init__()
        self.sequences = {}


class Reference(Model, bases.Reference, sequences.ReferenceSequencesMixin):

    annotation = Parent(Annotation, related_name='references')


class Gene(Model, bases.Gene):

    reference = Parent(Reference, related_name='genes')


class Transcript(Model, bases.Transcript, sequences.TranscriptSequencesMixin):

    gene = Parent(Gene, related_name='transcripts')

    @property
    def reference(self):
        return self.gene.reference


class Exon(Model, bases.Exon):

    transcript = Parent(Transcript, related_name='exons')

    @property
    def reference(self):
        return self.transcript.gene.reference


class CodingSequence(bases.CodingSequence, sequences.CodingSequencesMixin):

    def __init__(self, start, end):
        self._transcript = None
        super(CodingSequence, self).__init__(start, end)

    @property
    def transcript(self):
        return self._transcript

    @transcript.setter
    def transcript(self, value):
        if self._transcript:
            self._transcript.coding_sequence = None

        if value:
            self._transcript = value
            self._transcript.coding_sequence = self
