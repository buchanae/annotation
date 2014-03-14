# TODO handle multipe parents when linking
from __future__ import absolute_import

from annotation import models
from annotation.builder import Builder
from annotation.readers.gff import handlers


class ReaderBase(object):

    Builder = Builder

    def read(self, records):
        builder = self.Builder()
        self._init_builder(builder)
        builder.build(records)

    def _init_builder(self, builder):
        for handler in self._handlers:
            print handler
            handler.init_builder(builder)


class Reader(ReaderBase):

    def __init__(self, models=models, handlers=handlers):
        self.models = models
        self.handlers = handlers

        # For brevity:
        h = self.handlers
        m = self.models

        # Initialize handlers
        self.reference_handler = h.ReferenceHandler(m.Reference)
        self.gene_handler = h.GeneHandler(m.Gene, m.Reference)
        self.transcript_handler = h.TranscriptHandler(m.Transcript, m.Gene)
        self.exon_handler = h.ExonHandler(m.Exon, m.Transcript)

        cds_h = h.CodingSequenceHandler(m.CodingSequence, m.Transcript)
        self.coding_sequence_handler = cds_h

        self._handlers = [
            self.reference_handler,
            self.gene_handler,
            self.transcript_handler,
            self.exon_handler,
            self.coding_sequence_handler,
        ]

    def read(self, records):
        super(Reader, self).read(records)
        return self.reference_handler.references


# Goals:
# 1. easy access to adding a recognized type
#    reader.reference_handler.types.add('region')
# DONE

# 2. reuseable models across multiple file format readers
#    gff_reader = GFFReader(models)
#    genbank_reader = GenBankReader(models)
# DONE

# 3. ability to add new handlers (e.g. coding sequence)
# DONE
#    Requires subclassing Reader to initialize new handlers
#    that's a good thing, because it makes the handler variables
#    and the reader definition explicit, and it's not a ton
#    of work to subclass and add some simple calls to __init__


# 4. ability to easily override just one model in the set
# DONE


# 5. tend towards ease of use over ultimate power
# DONE

# 6. make it clear what happens when a reader is used twice
# a reader may be resused and the records from each call to read()
# (i.e. separate build) are unrelated)

#7. write a genbank reader to prove the reusability
# TODO make this reusable and write a GenBank reader

#8. Listing genes should match the order in the gff file?

_default_reader = Reader()
read = _default_reader.read
