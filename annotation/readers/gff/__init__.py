# TODO handle multipe parents when linking
from __future__ import absolute_import

from gff import GFF

from annotation.build import Builder
from annotation.models import default_models
from annotation.readers.gff.handlers import default_handlers
from annotation.readers.gff.types import default_types


class Reader(object):

    Builder = Builder

    def __init__(self, models=None, types=None, handlers=None):
        self.models = models or dict(default_models)
        self.types = types or dict(default_types)
        self.handlers = dict(default_handlers)

    def init_builder(self, builder):
        for handler in self._handlers.values():
            try:
                init = handler.init_builder
            except AttributeError:
                pass
            else:
                init(builder, self.models, self.types)

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


# 6. make it clear what happens when a reader is used twice
# a reader may be resused and the records from each call to read()
# (i.e. separate build) are unrelated)
#
# this just needs documentation at this point
#
# the opposite behavior could easily be created by moving the init_builder
# lines to __init__, which is pretty cool

#8. Listing genes should match the order in the gff file?
#
# I think this requires modifying the parent/child relationship mechanism


# 9. Possibly ditch AnnotationHandler and go with Annotation.from_gff

_default_reader = Reader()
read = _default_reader.read
read_file = _default_reader.read_file
read_path = _default_reader.read_path
