from annotation.readers.gff.core import Handler, Linker


def restrict_record_types(types, decode_fn):
    def fn(record, *args, **kwargs):
        if record.type in types:
            return decode_fn(record, *args, **kwargs)
    return fn


class AnnotationHandler(object):

    def __init__(self, Annotation, Reference):
        self.Annotation = Annotation
        self.Reference = Reference

    def init_builder(self, builder):
        self.annotation = self.Annotation()
        builder.post_transform.append(self.link_references)

    def link_references(self, node, record):
        if isinstance(node, self.Reference):
            node.annotation = self.annotation


class ReferenceHandler(object):

    def __init__(self, Reference):
        self.Reference = Reference
        self.types = {
            'reference',
            'chromosome',
            'contig',
        }

        self.decoder = restrict_record_types(self.types, self.decode)

    def init_builder(self, builder):
        builder.transform.append(self.decoder)

    def decode(self, record):
        return self.Reference(record.ID, record.end)


class GeneHandler(object):

    def __init__(self, Gene, Reference):
        self.Gene = Gene
        self.types = {
            'gene',
            'pseudogene',
            'transposable_element_gene',
        }

        self.decoder = restrict_record_types(self.types, self.decode)
        self.linker = Linker(Reference, Gene, 'reference', self.reference_ID)

    def init_builder(self, builder):
        builder.transform.append(self.decoder)
        builder.add_handler(self.linker)

    def decode(self, record):
        return self.Gene(record.ID, record.strand)

    def reference_ID(self, feature, record):
        return record.parent_ID or record.seqid


class TranscriptHandler(object):

    def __init__(self, Transcript, Gene):
        self.Transcript = Transcript
        self.types = {
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

        self.decoder = restrict_record_types(self.types, self.decode)
        self.linker = Linker(Gene, Transcript, 'gene')

    def init_builder(self, builder):
        builder.transform.append(self.decoder)
        builder.add_handler(self.linker)

    def decode(self, record):
        return self.Transcript(record.ID)


class ExonHandler(object):

    def __init__(self, Exon, Transcript):
        self.Exon = Exon
        self.types = {
            'exon',
            'pseudogenic_exon',
        }

        self.decoder = restrict_record_types(self.types, self.decode)
        self.linker = Linker(Transcript, Exon, 'transcript')

    def init_builder(self, builder):
        builder.transform.append(self.decoder)
        builder.add_handler(self.linker)

    def decode(self, record):
        return self.Exon(record.start, record.end)


class CodingSequenceHandler(object):

    class NotResolved(Exception): pass

    def __init__(self, CodingSequence, Transcript):
        self.CodingSequence = CodingSequence
        self.Transcript = Transcript
        self.types = {'CDS'}
        self.transcripts = {}
        self.deferred = []

        self.decoder = restrict_record_types(self.types, self.decode)

    def init_builder(self, builder):
        builder.transform.append(self.decoder)
        builder.add_handler(self)

    def decode(self, record):
        return self.CodingSequence(record.start, record.end)

    def transform(self, record):
        if record.type in self.types:
            try:
                self.resolve(record)
            except self.NotResolved:
                self.deferred.append(record)

    # TODO could take a hint from angular and allow this to be returned from
    #      the transform function, which would give it access to the node and
    #      record explicitly
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
                cds = self.decode(record)
                cds.transcript = transcript
            else:
                cds = transcript.coding_sequence
                cds.start = min(cds.start, record.start)
                cds.end = max(cds.end, record.end)
