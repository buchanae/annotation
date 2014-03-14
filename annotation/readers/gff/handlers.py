from annotation.readers.gff.core import Handler, Linker

class ReferenceHandler(Handler):

    types = {
        'reference',
        'chromosome',
        'contig',
    }

    def __init__(self, builder, models):
        super(ReferenceHandler, self).__init__(builder, models)
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
        super(GeneHandler, self).__init__(builder, models)
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
        super(CodingSequenceHandler, self).__init__(builder, models)
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
                cds = self.decode(record)
                cds.transcript = transcript
            else:
                cds = transcript.coding_sequence
                cds.start = min(cds.start, record.start)
                cds.end = max(cds.end, record.end)
