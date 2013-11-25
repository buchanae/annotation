from __future__ import absolute_import

import logging

from annotation.builders.core import AnnotationBuilder
from annotation.builders.linker import Linker


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


_multiple_parents_error_msg = "A record with multiple parents was found. Currently this library doesn't know how to handle that. Try using FirstParentLinker."

class MultipleParentsError(Exception):
    def __init__(self):
        super(MultipleParentsError, self).__init__(_multiple_parents_error_msg)

# TODO handle multipe parents when linking


class Decoder(object):
    def __init__(self, decode_fn, types=None):
        self.decode_fn = decode_fn
        self.types = types

    def transform(self, record):
        if record.type in self.types:
            return self.decode_fn(record)


class GFFLinker(Linker):

    def __init__(self, parent_type, child_type, parent_attr):
        super(GFFLinker, self).__init__()
        self.parent_type = parent_type
        self.child_type = child_type
        self.parent_attr = parent_attr

    def _get_ID(self, node, record):
        return node.ID

    def _get_parent_ID(self, node, record):
        try:
            model_method_name = 'GFF_' + self.parent_attr + '_ID'
            model_method = getattr(node, model_method_name, None)
            if model_method:
                return model_method(record)
            else:
                return record.parent_ID
        except gff.MultipleParents:
            raise MultipleParentsError()

    def _link(self, child, parent):
        setattr(child, self.parent_attr, parent)

    def _index_parent(self, node, record):
        if isinstance(node, self.parent_type):
            super(GFFLinker, self)._index_parent(node, record)

    def _try_link(self, node, record):
        if isinstance(node, self.child_type):
            super(GFFLinker, self)._try_link(node, record)


class FirstParentLinker(GFFLinker):
    def _get_parent_ID(self, node, record):
        try:
            return super(FirstParentLinker, self)._get_parent_ID(node, record)
        except MultipleParentsError:
            return record.parent_IDs[0]


class GFFBuilderError(Exception): pass


class DefaultGFFBuilder(AnnotationBuilder):

    # TODO consider moving this to a defaultdict(list)
    Reference_types = REFERENCE_TYPES
    Gene_types = GENE_TYPES
    Transcript_types = TRANSCRIPT_TYPES
    Exon_types = EXON_TYPES

    Decoder = Decoder
    Linker = GFFLinker

    def __init__(self, Annotation):
        super(DefaultGFFBuilder, self).__init__(Annotation)

        self._register_decoder('Reference')
        self._register_decoder('Gene')
        self._register_decoder('Transcript')
        self._register_decoder('Exon')

        self._register_linker('Reference', 'Gene')
        self._register_linker('Gene', 'Transcript')
        self._register_linker('Transcript', 'Exon')

    def _get_feature_class(self, name):
        try:
            return getattr(self.Annotation, name)
        except AttributeError:
            tpl = "Annotation doesn't have a {} type"
            msg = tpl.format(name)
            raise GFFBuilderError(msg)

    def _register_decoder(self, name):
        """A helper function for registering decoders."""

        feature_cls = self._get_feature_class(name)

        try:
            from_GFF_func = getattr(feature_cls, 'from_GFF')
        except AttributeError:
            tpl = "{} doesn't have a from_GFF method"
            msg = tpl.format(name)
            raise GFFBuilderError(msg)

        types_name = name + '_types'
        types = getattr(self, types_name, [])

        decoder = self.Decoder(from_GFF_func, types)
        decoder_name = name + '_decoder'
        setattr(self, decoder_name, decoder)

        self.builder.handlers.append(decoder)

    def _register_linker(self, parent_name, child_name):
        parent_feature_cls = self._get_feature_class(parent_name)
        child_feature_cls = self._get_feature_class(child_name)

        parent_attr_name = parent_name.lower()

        linker = self.Linker(parent_feature_cls, child_feature_cls,
                             parent_attr_name)

        linker_name = '{}_{}_linker'.format(parent_name, child_name)
        setattr(self, linker_name, linker)

        self.builder.handlers.append(linker)

    def from_GFF(self, records):
        return self.builder.build(records)
