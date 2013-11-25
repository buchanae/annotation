from __future__ import absolute_import

from annotation import models
from annotation.builders.gff import DefaultGFFBuilder


class Annotation(object):
    Reference = models.Reference
    Gene = models.Gene
    Transcript = models.Transcript
    Exon = models.Exon

    GFFBuilder = DefaultGFFBuilder

    def __init__(self):
        self.gff_builder = self.GFFBuilder(self)

    @classmethod
    def from_GFF(cls, records):
        return cls().gff_builder.from_GFF(records)
