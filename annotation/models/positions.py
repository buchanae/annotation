import logging
# TODO this could be used to nicely hide
#      the details of 1-based vs 0-based systems?

# TODO are these better as functions?

log = logging.getLogger(__name__)


# TODO __slots__
class GenomicPosition(int):

    def __new__(cls, pos=None, reverse_strand=False):
        if pos is None:
            pos = 1

        obj = super(GenomicPosition, cls).__new__(cls, pos)
        obj._pos = pos
        obj.reverse_strand = reverse_strand
        return obj

    @classmethod
    def from_zero_based(cls, pos):
        return cls(pos + 1)

    def upstream(self, distance):
        if self.reverse_strand:
            return GenomicPosition(self + distance, self.reverse_strand)
        else:
            return GenomicPosition(self - distance, self.reverse_strand)

    def downstream(self, distance):
        if self.reverse_strand:
            return GenomicPosition(self - distance, self.reverse_strand)
        else:
            return GenomicPosition(self + distance, self.reverse_strand)

    def __add__(self, other):
        if isinstance(other, GenomicPosition):
            if other.reverse_strand != self.reverse_strand:
                # TODO better message here
                raise ValueError('Strands conflict')
            other = other._pos
        return GenomicPosition(self._pos + other)

    __radd__ = __add__


class GenomicPositionDescriptor(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, cls=None):
        value = getattr(obj, self.name, None)
        return GenomicPosition(value, obj.reverse_strand)

    def __set__(self, obj, value):
        if isinstance(value, GenomicPosition):
            value = value._pos
        elif not isinstance(value, int):
            # TODO nicer error
            msg = 'Trying to set genomic position with an unrecognized type: {}'
            msg = msg.format(type(value))
            raise ValueError(msg)

        setattr(obj, self.name, value)
