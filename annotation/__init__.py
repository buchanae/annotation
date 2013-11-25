from __future__ import absolute_import

from annotation import models
from annotation.builders.gff import DefaultGFFBuilder


class ReferenceLinker(object):
    def __init__(self, Reference, anno):
        self.Reference = Reference
        self.anno = anno

    def post_transform(self, node, record):
        if isinstance(node, self.Reference):
            node.annotation = self.anno


class Annotation(models.Annotation):
    Reference = models.Reference
    Gene = models.Gene
    Transcript = models.Transcript
    Exon = models.Exon

    GFFBuilder = DefaultGFFBuilder

    def __init__(self):
        super(Annotation, self).__init__()

        self.gff_builder = self.GFFBuilder(self)
        self.reference_linker = ReferenceLinker(self.Reference, self)
        self.gff_builder.builder.handlers.append(self.reference_linker)

    # TODO this is getting in the way
    #      should from_GFF be an instance method? what if you import multiple times?
    #      importing multiple times could be useful?
    #      that would mean maintaining a per-annotation relationship index,
    #      and changing the way model relationships work.
    #      would probably turn out to be a great change though,
    #      allowing more power (think annotation.lookup('some-feature-ID'))
    #      and easier compatiblity with a database.
    @classmethod
    def from_GFF(cls, records):
        anno = cls()
        anno.gff_builder.from_GFF(records)
        return anno
