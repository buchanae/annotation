# TODO handle multipe parents when linking
from __future__ import absolute_import

from gff import GFF

from annotation import models
from annotation.builder import Builder
from annotation.readers.gff import handlers
from annotation.readers.gff.types import default_types


class Reader(object):

    Builder = Builder

    def __init__(self, models=models, types=default_types, handlers=handlers):
        self._models = models
        self._types = types
        self._handlers = handlers

    def init_builder(self, builder):
        # For brevity:
        b = builder
        m = self._models
        t = self._types
        h = self._handlers

        # Initialize handlers
        anno_handler = h.AnnotationHandler(b, m.Annotation, m.Reference)
        h.ReferenceHandler(b, m.Reference, t.Reference)
        h.GeneHandler(b, m.Gene, m.Reference, t.Gene)
        h.TranscriptHandler(b, m.Transcript, m.Gene, t.Transcript)
        h.ExonHandler(b, m.Exon, m.Transcript, t.Exon)
        h.CodingSequenceHandler(b, m.CodingSequence, m.Transcript,
                                t.CodingSequence)

        # Return the annotation handler, which gives us access to the 
        # Annotation instance after the build completes
        return anno_handler

    def read(self, records):
        builder = self.Builder()
        anno_handler = self.init_builder(builder)
        builder.build(records)
        return anno_handler.annotation

    def read_file(self, file_handle):
        records = GFF.from_file(file_handle)
        return self.read(records)

    def read_path(self, path):
        with open(path) as file_handle:
            return self.read_file(file_handle)


# Goals:
# 1. easy access to adding a recognized type
#   class MyTypes(DefaultTypes):
#       def  __init__(self):
#           super(MyTypes, self).__init__()
#           self.Transcript.add('foo')
#
#   reader = Reader(types=MyTypes())
#
# OR
#   annotation.readers.gff.default_types.Transcript.add('foo')
#   which would make a global change
#
# OR I guess you could subclass a handler and hardcode the types there
#    although that doesn't seem nice


# 2. reuseable models across multiple file format readers
#    gff_reader = GFFReader(models)
#    genbank_reader = GenBankReader(models)
# DONE

# 3. ability to add new handlers (e.g. coding sequence)
# DONE
#    Requires subclassing Reader to initialize new handlers;
#    that's a good thing, because it makes the handler variables
#    and the reader definition explicit, and it's not a ton
#    of work to subclass and add some simple calls to init_builder


# 4. ability to easily override just one model in the set
# DONE


# 5. tend towards ease of use over ultimate power
# DONE

# 6. make it clear what happens when a reader is used twice
# a reader may be resused and the records from each call to read()
# (i.e. separate build) are unrelated)
#
# this just needs documentation at this point
#
# the opposite behavior could easily be created by moving the init_builder
# lines to __init__, which is pretty cool

#7. write a genbank reader to prove the reusability
# TODO make this reusable and write a GenBank reader

#8. Listing genes should match the order in the gff file?
#
# I think this requires modifying the parent/child relationship mechanism


# 9. Possibly ditch AnnotationHandler and go with Annotation.from_gff

_default_reader = Reader()
read = _default_reader.read
read_file = _default_reader.read_file
read_path = _default_reader.read_path
