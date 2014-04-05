from collections import defaultdict
import functools

from annotation.readers.gff.linker import Linker


def restrict_record_types(types, decode_fn):
    def fn(record, *args, **kwargs):
        if record.type in types:
            return decode_fn(record, *args, **kwargs)
    return fn


def decode(model_name, types):
    def decorator(decode_fn):

        def init_builder(builder, models, types):
            model_class = getattr(models, model_name)
            allowed_types = getattr(types, model_name)
            partial_decode_fn = functools.partial(model_class)
            fn = restrict_record_types(allowed_types, partial_decode_fn)
            builder.transform.append(fn)

        decode_fn.init_builder = init_builder
        return decode_fn

    return decorator


def link(parent_type_name, child_type_name, parent_key=None, Linker=Linker):
    def decorator(link_fn):

        def init_builder(builder, models, types):
            parent_type = getattr(models, parent_type_name)
            child_type = getattr(models, child_type_name)

            linker = Linker(parent_type, child_type, link_fn, parent_key)
            builder.add_handler(linker)

        link_fn.init_builder = init_builder
        return link_fn

    return decorator


@decode('Reference')
def decode_reference(Reference, record):
    return Reference(record.ID, record.end)


@decode('Gene')
def decode_gene(Gene, record):
    return Gene(record.ID, record.strand)


def reference_ID(feature, record):
    return record.parent_ID or record.seqid


@link('Reference', 'Gene', parent_key=reference_ID)
def link_gene_reference(gene, reference):
    gene.reference = reference


@decode('Transcript')
def decode_transcript(Transcript, record):
    return Transcript(record.ID)


@link('Gene', 'Transcript')
def link_gene_transcript(transcript, gene):
    transcript.gene = gene


@decode('Exon')
def decode_exon(Exon, record):
    return Exon(record.start, record.end)


@link('Transcript', 'Exon')
def link_transcript_exon(exon, transcript):
    exon.transcript = transcript


@decode('CodingSequence')
def decode_cds(CodingSequence, record):
    return CodingSequence(record.start, record.end)


@link('Transcript', 'CodingSequence')
def link_transcript_cds(cds, transcript):
    if not transcript.cds:
        transcript.cds = cds
        cds.transcript = transcript
    else:
        transcript.cds.start = min(transcript.cds.start, cds.start)
        transcript.cds.end = max(transcript.cds.end, cds.end)


default_handlers = {}
for key, value in locals().items():
    if hasattr(value, 'init_builder'):
        default_handlers[value.__name__] = value
