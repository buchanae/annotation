import functools


class HandlerBase(object):

    fields = 'seqid source type start end score strand phase attributes'.split()

    def __init__(self, builder, node_type, GFFRecord, defaults=None):
        self.node_type = node_type
        self.GFFRecord = GFFRecord
        self.defaults = defaults or {}

        transform = self.match_node_type(self.transform)
        builder.transform.append(transform)

    def match_node_type(self, fn):
        @functools.wraps(fn)
        def wrapper(node, *args, **kwargs):
            if isinstance(node, self.node_type):
                return fn(node, *args, **kwargs)
        return wrapper

    def make_record(self, **kwargs):
        values = dict(self.defaults)
        values.update(kwargs)

        args = []
        for field in self.fields:
            arg = values.get(field)
            args.append(arg)

        # Create GFF record object
        return self.GFFRecord(*args)

    def transform(self, obj):
        raise NotImplementedError()


class ReferenceHandler(HandlerBase):

    def transform(self, ref):
        r = self.make_record()

        r.seqid = ref.ID
        r.type = 'reference'
        r.start = 1
        r.end = ref.size
        r.ID = ref.ID
        r.attributes['Name'] = ref.ID

        yield r


class GeneHandler(HandlerBase):

    def transform(self, gene):
        r = self.make_record()

        r.seqid = gene.reference.ID
        r.type = 'gene'
        r.start = gene.start
        r.end = gene.end
        r.strand = '-' if gene.reverse_strand else '+'
        r.ID = gene.ID
        r.parent_ID = gene.reference.ID
        r.attributes['Name'] = gene.ID

        yield r


class TranscriptHandler(HandlerBase):

    # TODO handle coding vs non-coding
    def transform(self, transcript):
        r = self.make_record()

        r.seqid = transcript.gene.reference.ID
        r.type = 'transcript'
        r.start = transcript.start
        r.end = transcript.end
        r.strand = transcript.strand
        r.ID = transcript.ID
        r.parent_ID = transcript.gene.ID
        r.attributes['Name'] = transcript.ID

        yield r


class ExonHandler(HandlerBase):

    def transform(self, exon):
        r = self.make_record()

        r.seqid = exon.transcript.gene.reference.ID
        r.type = 'exon'
        r.start = exon.start
        r.end = exon.end
        r.strand = exon.strand
        r.parent_ID = exon.transcript.ID

        yield r


class CodingSequenceHandler(HandlerBase):

    def transform(self, cds):
        r = self.make_record()

        # TODO produce multiple. Possibly also produce UTR records,
        #      although possibly those deserve their own handler.
        # TODO handle phase
        r.seqid = cds.transcript.gene.reference.ID
        r.type = 'CDS'
        r.start = TODO
        r.end = TODO
        r.strand = cds.transcript.strand
        r.parent_ID = cds.transcript.ID

        yield r
