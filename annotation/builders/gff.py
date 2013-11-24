from __future__ import absolute_import

import logging

import gff

from annotation.builders.core import Builder, Handler, Linker


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

# TODO handle multipe parents when linking


class Decoder(Handler):
    def __init__(self, decode_fn, types=None):
        self.decode_fn = decode_fn
        self.types = types

    def transform(self, record):
        if record.type in self.types:
            return self.decode_fn(record)


class AnnotationBuilder(object):
    Builder = Builder

    def __init__(self, Annotation):
        self.builder = self.Builder()
        self.Annotation = Annotation


class GFFBuilder(AnnotationBuilder):
    GFF = gff.GFF

    def from_file(self, fh):
        records = self.GFF.from_stream(fh)
        return self.builder.build(records)


class DefaultGFFBuilder(GFFBuilder):
    Reference_types = REFERENCE_TYPES
    Gene_types = GENE_TYPES

    def __init__(self, Annotation):
        super(DefaultGFFBuilder, self).__init__(Annotation)

        self.reference_decoder = Decoder(Annotation.Reference.from_GFF,
                                         types=self.Reference_types)

        self.gene_decoder = Decoder(Annotation.Gene.from_GFF, types=self.Gene_types)

        self.linker = Linker()
        self.linker.add_pattern('reference')

        self.builder.handlers.extend([
            self.reference_decoder,
            self.gene_decoder,
            self.linker,
        ])
