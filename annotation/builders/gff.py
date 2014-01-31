# TODO handle multipe parents when linking
from __future__ import absolute_import

import logging

from annotation import models
from annotation.builders.core import Builder as BuilderBase
from annotation.builders.linker import Linker as LinkerBase


log = logging.getLogger(__name__)


class Linker(LinkerBase):

    def __init__(self, parent_type, child_type, parent_attr,
                 parent_ID_func=None):

        super(Linker, self).__init__()
        self.parent_type = parent_type
        self.child_type = child_type
        self.parent_attr = parent_attr
        self.parent_ID_func = parent_ID_func

    def _get_ID(self, node, record):
        return node.ID

    def _get_parent_ID(self, node, record):
        if self.parent_ID_func:
            return self.parent_ID_func(node, record)
        else:
            return record.parent_ID

    def _link(self, child, parent):
        setattr(child, self.parent_attr, parent)

    def _index_parent(self, node, record):
        if isinstance(node, self.parent_type):
            super(Linker, self)._index_parent(node, record)

    def _try_link(self, node, record):
        if isinstance(node, self.child_type):
            super(Linker, self)._try_link(node, record)


class Handler(object):

    Linker = Linker

    def add_decoder(self, decode_fn, types):
        def fn(record):
            if record.type in types:
                return decode_fn(record)
        self.builder.transforms.append(fn)

    def add_linker(self, *args, **kwargs):
        linker = self.Linker(*args, **kwargs)
        self.builder.add_handler(linker)

    def __init__(self, builder, models):
        self.builder = builder
        try:
            decode_fn = getattr(self, 'decode')
            types = getattr(self, 'types')
            self.add_decoder(decode_fn, types)
        except AttributeError:
            pass


class ReferenceHandler(Handler):

    types = {
        'reference',
        'chromosome',
        'contig',
    }

    def __init__(self, builder, models):
        super(ReferenceHandler, self).__init__(builder)
        self.Reference = models.Reference

    def decode(self, record):
        return self.Reference(record.ID, record.end)


class GeneHandler(Handler):

    types = {
        'gene',
        'pseudogene',
        'transposable_element_gene',
    }

    def __init__(self, builder, models):
        super(GeneHandler, self).__init__(builder)
        self.Gene = models.Gene
        self.add_linker(models.Reference, models.Gene, 'reference',
                        self.reference_ID)

    def decode(self, record):
        return self.models.Gene(record.ID, record.strand)

    def reference_ID(self, feature, record):
        return record.parent_ID or record.seqid


class TranscriptHandler(Handler):

    types = {
        'mRNA',
        'snRNA', 
        'rRNA',
        'snoRNA',
        'mRNA_TE_gene',
        'miRNA',
        'tRNA',
        'ncRNA',
        'pseudogenic_transcript',
    }

    def __init__(self, builder, models):
        super(TranscriptHandler, self).__init__(builder, models)
        self.Transcript = models.Transcript
        self.add_linker(models.Gene, models.Transcript, 'gene')

    def decode(self, record):
        return self.Transcript(record.ID)


class ExonHandler(Handler):

    types = {
        'exon',
        'pseudogenic_exon',
    }

    def __init__(self, builder, models):
        super(ExonHandler, self).__init__(builder, models)
        self.Exon = models.Exon
        self.add_linker(models.Transcript, models.Exon, 'transcript')

    def decode(self, record):
        return self.Exon(record.start, record.end)


class CodingSequenceHandler(Handler):

    types = {'CDS'}

    class NotResolved(Exception): pass

    def __init__(self, builder, models):
        super(CodingSequence, self).__init__(builder, models)
        self.CodingSequence = models.CodingSequence
        self.Transcript = models.Transcript
        self.transcripts = {}
        self.deferred = []
        builder.add_handler(self)

    def decode(self, record):
        return self.CodingSequence(record.start, record.end)

    def transform(self, record):
        if record.type in self.types:
            try:
                self.resolve(record)
            except self.NotResolved:
                self.deferred.append(record)

    def post_transform(self, node, record):
        if isinstance(node, self.Transcript):
            self.transcripts[node.ID] = node

            for record in self.deferred:
                try:
                    self.resolve(record)
                    self.deferred.remove(record)
                except self.NotResolved:
                    pass

    def finalize(self):
        for record in self.deferred:
            try:
                self.resolve(record)
            except self.NotResolved:
                log.warning('Never resolved: {}'.format(record))

    def resolve(self, record):
        parent_ID = record.parent_ID
        try:
            transcript = self.transcripts[parent_ID]
        except KeyError:
            raise self.NotResolved()
        else:
            if not transcript.coding_sequence:
                cds = self.CodingSequence_from_GFF(record)
                cds.transcript = transcript
            else:
                cds = transcript.coding_sequence
                cds.start = min(cds.start, record.start)
                cds.end = max(cds.end, record.end)


class Reader(object):

    Builder = Builder

    handlers = [
        ReferenceHandler,
        GeneHandler,
        TranscriptHandler,
        ExonHandler,
        CodingSequenceHandler,
    ]

    class Models:
        Reference = models.Reference
        Gene = models.Gene
        Transcript = models.Transcript
        Exon = models.Exon
        CodingSequence = models.CodingSequence

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
