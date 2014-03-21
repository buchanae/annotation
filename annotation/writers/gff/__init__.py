import gff as gfflib

from annotation import models
from annotation.build import Builder
from annotation.writers.gff import handlers


class Writer(object):

    Builder = Builder

    def __init__(self, defaults=None, models=models, handlers=handlers,
                 GFFRecord=gfflib.GFF):

        self.defaults = defaults or {}

        self._models = models
        self._handlers = handlers
        self._GFFRecord = GFFRecord

    def init_builder(self, builder):
        # For brevity:
        b = builder
        m = self._models
        h = self._handlers
        GFF = self._GFFRecord
        d = self.defaults

        h.ReferenceHandler(b, m.Reference, GFF, d)
        h.GeneHandler(b, m.Gene, GFF, d)
        h.TranscriptHandler(b, m.Transcript, GFF, d)
        h.ExonHandler(b, m.Exon, GFF, d)
        h.CodingSequenceHandler(b, m.CodingSequence, GFF, d)

    def write(self, file_handle, objects):
        builder = self.Builder()
        self.init_builder(builder)

        for res in builder.build(objects):
            print 'res'
            s = str(res) + '\n'
            file_handle.write(s)


_default_writer = Writer()
write = _default_writer.write
