from collections import defaultdict

from annotation.readers.gff.linker import Linker


def restrict_record_types(types, decode_fn):
    def fn(record, *args, **kwargs):
        if record.type in types:
            return decode_fn(record, *args, **kwargs)
    return fn


class AnnotationHandler(object):

    def __init__(self, builder, Annotation, Reference):
        self.Annotation = Annotation
        self.Reference = Reference

        # init builder
        self.annotation = self.Annotation()
        builder.post_transform.append(self.link_references)

    def link_references(self, node, record):
        if isinstance(node, self.Reference):
            node.annotation = self.annotation


class ReferenceHandler(object):

    def __init__(self, builder, Reference, types):
        self.Reference = Reference
        self.types = types
        self.decoder = restrict_record_types(self.types, self.decode)

        # init builder
        builder.transform.append(self.decoder)

    def decode(self, record):
        return self.Reference(record.ID, record.end)


class GeneHandler(object):

    def __init__(self, builder, Gene, Reference, types):
        self.Gene = Gene
        self.types = types
        self.decoder = restrict_record_types(self.types, self.decode)
        self.linker = Linker(Reference, Gene, 'reference', self.reference_ID)

        # init builder
        builder.transform.append(self.decoder)
        builder.add_handler(self.linker)

    def decode(self, record):
        return self.Gene(record.ID, record.strand)

    def reference_ID(self, feature, record):
        return record.parent_ID or record.seqid


class TranscriptHandler(object):

    def __init__(self, builder, Transcript, Gene, types):
        self.Transcript = Transcript
        self.types = types
        self.decoder = restrict_record_types(self.types, self.decode)
        self.linker = Linker(Gene, Transcript, 'gene')

        # init builder
        builder.transform.append(self.decoder)
        builder.add_handler(self.linker)

    def decode(self, record):
        return self.Transcript(record.ID)


class ExonHandler(object):

    def __init__(self, builder, Exon, Transcript, types):
        self.Exon = Exon
        self.types = types
        self.decoder = restrict_record_types(self.types, self.decode)
        self.linker = Linker(Transcript, Exon, 'transcript')

        # init builder
        builder.transform.append(self.decoder)
        builder.add_handler(self.linker)

    def decode(self, record):
        return self.Exon(record.start, record.end)


class CodingSequenceHandler(object):

    def __init__(self, builder, CodingSequence, Transcript, types):
        self.CodingSequence = CodingSequence
        self.Transcript = Transcript
        self.types = types

        # init builder
        self.transcripts = {}
        self.start_end_by_parent = {}
        collector = restrict_record_types(self.types, self.collect)
        builder.transform.append(collector)
        builder.add_handler(self)

    def collect(self, record):
        # TODO you end up storing every cds min/max
        parent_ID = record.parent_ID
        default = 0, 0
        start, end = self.start_end_by_parent.get(parent_ID, default)
        start, end = min(start, record.start), max(end, record.end)
        self.start_end_by_parent[parent_ID] = start, end

    def post_transform(self, node, record):
        if isinstance(node, self.Transcript):
            self.transcripts[node.ID] = node

    def finalize(self):
        for transcript_ID, transcript in self.transcripts.items():
            try:
                start, end = self.start_end_by_parent[transcript_ID]
            except KeyError:
                pass
            else:
                cds = self.CodingSequence(start, end)
                cds.transcript = transcript
