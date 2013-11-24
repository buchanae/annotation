from __future__ import absolute_import

import logging

import gff

from annotation.builders.core import AnnotationBuilder, Handler, Linker


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


_multiple_parents_error_msg = "A record with multiple parents was found. Currently this library doesn't know how to handle that. Try using FirstParentRule."

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


class GFFBuilder(AnnotationBuilder):
    GFF = gff.GFF

    def from_file(self, fh):
        records = self.GFF.from_stream(fh)
        return self.builder.build(records)


class Rule(object):
    def __init__(self, cls, parent_attr):
        self.cls = cls
        self.parent_attr = parent_attr

    def match(self, node, record):
        return isinstance(node, self.cls)

    def get_parent_ID(self, node, record):
        try:
            model_method_name = 'GFF_' + self.parent_attr + '_ID'
            model_method = getattr(node, model_method_name, None)
            if model_method:
                model_method(record)
            else:
                return record.parent_ID
        except gff.MultipleParents:
            raise MultipleParentsError()


class FirstParentRule(Rule):
    def get_parent_ID(self, node, record):
        try:
            return super(FirstParentRule, self).get_parent_ID(node, record)
        except MultipleParentsError:
            return record.parent_IDs[0]


class GFFLinker(Linker):
    def __init__(self, rules=None):
        super(GFFLinker, self).__init__()
        self.rules = rules or []

    def _link(self, node, record):
        for rule in self.rules:
            if rule.match(node, record):
                parent_ID = rule.get_parent_ID(node, record)
                if parent_ID:
                    parent = self._index[parent_ID]
                    setattr(node, rule.parent_attr, parent)


# TODO GFFBuilder name conflicts with core.Builder since it's not a subclass
class GFFBuilderError(Exception): pass

class DefaultGFFBuilder(GFFBuilder):

    Reference_types = REFERENCE_TYPES
    Gene_types = GENE_TYPES
    Transcript_types = TRANSCRIPT_TYPES
    Exon_types = EXON_TYPES

    Decoder = Decoder
    Linker = GFFLinker

    def _register_decoder(self, name):
        """A helper function for registering decoders."""

        try:
            feature_cls = getattr(self.Annotation, name)
        except AttributeError:
            tpl = "Annotation doesn't have a {} type"
            msg = tpl.format(name)
            raise GFFBuilderError(msg)

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

    def __init__(self, Annotation):
        super(DefaultGFFBuilder, self).__init__(Annotation)

        self._register_decoder('Reference')
        self._register_decoder('Gene')
        self._register_decoder('Transcript')
        self._register_decoder('Exon')

        # TODO add rules as attributes to this class
        self.linker = self.Linker([
            Rule(Annotation.Gene, 'reference'),
            Rule(Annotation.Transcript, 'gene'),
            Rule(Annotation.Exon, 'transcript'),
        ])

        self.builder.handlers.append(self.linker)
