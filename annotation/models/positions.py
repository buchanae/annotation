# TODO this could be used to nicely hide
#      the details of 1-based vs 0-based systems?

class GenomicPosition(int):
    def __new__(cls, pos=1, reverse_strand=False):
        if pos < 1:
            msg = "Genomic position can't be less than 1: {}".format(pos)
            raise ValueError(msg)

        obj = super(GenomicPosition, cls).__new__(cls, pos)
        obj._pos = pos
        obj.reverse_strand = reverse_strand
        return obj

    @classmethod
    def from_zero_based(cls, pos):
        return cls(pos + 1)

    def upstream(self, distance):
        if self.reverse_strand:
            return GenomicPosition(self + distance)
        else:
            return GenomicPosition(self - distance)

    def downstream(self, distance):
        if self.reverse_strand:
            return GenomicPosition(self - distance)
        else:
            return GenomicPosition(self + distance)

    def __add__(self, other):
        if isinstance(other, GenomicPosition):
            other = other._pos
        return GenomicPosition(self._pos + other)

    __radd__ = __add__


class GenomicPositionDescriptor(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, cls=None):
        return getattr(obj, self.name, GenomicPosition())

    def __set__(self, obj, value):
        if not isinstance(value, GenomicPosition):
            value = GenomicPosition(value)
        setattr(obj, self.name, value)
