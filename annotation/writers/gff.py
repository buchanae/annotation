from annotation.builder import Builder


class DefaultHandler(object):
    fields = 'seqid source type start end score strand phase attributes'.split()


    def __init__(self, GFF, defaults=None):
        self.GFF = GFF
        if defaults is None:
            defaults = {}

        self.defaults = defaults

    def transform(self, anno_obj):
        args = []
        for field in self.fields:
            arg = self.defaults.get(field)
            args.append(arg)

        gff_obj = self.GFF(*args)

        try:
            gff_obj.seqid = anno_obj.reference.ID
        except AttributeError:
            pass

        try:
            gff_obj.ID = anno_obj.ID
        except AttributeError:
            pass

        gff_obj.type = anno_obj.__class__.__name__.lower()

        for key in self.fields:
            value = getattr(anno_obj, key, None)
            if value:
                setattr(gff_obj, key, value)

        try:
            update_func = anno_obj.update_GFF
        except AttributeError:
            pass
        else:
            update_func(gff_obj)

        return gff_obj


class GFFExporter(Builder):

    def __init__(self, GFF):
        super(GFFExporter, self).__init__()
        self.defaults = {}
        self.default_handler = DefaultHandler(GFF, self.defaults)
        self.handlers.append(self.default_handler)
