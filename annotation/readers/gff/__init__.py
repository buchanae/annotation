# TODO handle multipe parents when linking
from __future__ import absolute_import

from annotation import models
from annotation.builder import Builder
from annotation.readers.gff import handlers


class ReaderBase(object):

    Builder = Builder

    def read(self, records):
        builder = self.Builder()

        for handler in self.handlers:
            handler(builder, self.Models)

        references = []
        def collect_references(node, record):
            if isinstance(node, self.Models.Reference):
                references.append(node)

        builder.post_transform.append(collect_references)

        builder.build(records)
        return references


class Reader(ReaderBase):

    handlers = [
        handlers.ReferenceHandler,
        handlers.GeneHandler,
        handlers.TranscriptHandler,
        handlers.ExonHandler,
        handlers.CodingSequenceHandler,
    ]

    class Models:
        Reference = models.Reference
        Gene = models.Gene
        Transcript = models.Transcript
        Exon = models.Exon
        CodingSequence = models.CodingSequence


_default_reader = Reader()
read = _default_reader.read
