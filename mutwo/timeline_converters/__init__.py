"""Convert :class:`mutwo.timeline_interfaces.TimeLine` to objects useable by other parts of `mutwo`."""

from .timelines import *
from . import timelines

__all__ = timelines.__all__

# Cleanup
del timelines
