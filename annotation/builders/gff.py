from __future__ import absolute_import

import logging

from gff import GFF

from annotation.builders.core import Builder, HandlerBase


REFERENCE_TYPES = [
    'reference',
    'chromosome',
    'contig',
]

GENE_TYPES = [
    'gene',
    'pseudogene',
    'transposable_element_gene',
]

TRANSCRIPT_TYPES = [
    'mRNA',
    'snRNA', 
    'rRNA',
    'snoRNA',
    'mRNA_TE_gene',
    'miRNA',
    'tRNA',
    'ncRNA',
    'pseudogenic_transcript',
]

EXON_TYPES = [
    'exon',
    'pseudogenic_exon',
]

log = logging.getLogger('annotation.builders.gff')



_multiple_parents_error_msg = "A record with multiple parents was found. Currently this library doesn't know how to handle that. Try using the MultipleParentsGeneHandler."

class MultipleParentsError(Exception):
    def __init__(self):
        super(MultipleParentsError, self).__init__(_multiple_parents_error_msg)


class GFFHandlerBase(HandlerBase):
    def parent_ID(self, record):
        parent_IDs = record.parent_IDs

        if parent_IDs:
            if len(parent_IDs) > 1:
                # Note: this library doesn't yet know how to handle multiple parents.
                #       We raise an exception to ensure the user knows that.
                raise MultipleParentsError()
            else:
                return parent_IDs[0]


class GeneHandlerBase(GFFHandlerBase):
    def parent_ID(self, record):
        # Sometimes gene records don't explicity set a "Parent" attribute
        # for their reference, so fall back to the seq ID in that case.
        parent_ID = super(GeneHandlerBase, self).parent_ID(record)
        return parent_ID or record.seqid


class GFFBuilder(Builder):

    from_records = Builder.build

    def from_file(self, path, root=None):
        with open(path) as fh:
            records = GFF.from_stream(fh)
            return self.from_records(records, root)


class DefaultGFFBuilder(GFFBuilder):

    def __init__(self, Reference, Gene, Transcript, Exon):

        # Define copies of our GFF feature type matchers
        self.reference_types = list(REFERENCE_TYPES)
        self.gene_types = list(GENE_TYPES)
        self.transcript_types = list(TRANSCRIPT_TYPES)
        self.exon_types = list(EXON_TYPES)

        # A couple helpers, for brevity
        make = GFFHandlerBase.make
        gene_make = GeneHandlerBase.make

        # Make our handler classes
        self.ReferenceHandler = make('ReferenceHandler', Reference)
        self.GeneHandler = gene_make('GeneHandler', Gene)
        self.TranscriptHandler = make('TranscriptHandler', Transcript)
        self.ExonHandler = make('ExonHandler', Exon)

        # And now instances of those handler classes
        self.reference_handler = self.ReferenceHandler(self.reference_types)
        self.gene_handler = self.GeneHandler(self.gene_types)
        self.transcript_handler = self.TranscriptHandler(self.transcript_types)
        self.exon_handler = self.ExonHandler(self.exon_types)

        super(DefaultGFFBuilder, self).__init__([
            self.reference_handler,
            self.gene_handler,
            self.transcript_handler,
            self.exon_handler,
        ])
