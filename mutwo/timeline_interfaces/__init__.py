"""Place events with absolute start and end times on a time line.

`Mutwo` events usually follow an approach of relative placement in time.
This means each event has a duration, and if there is a sequence of events
the second event will start after the first event finishes. So the start
and end time of any event dependent on all events which happens before the
given event. This package implements the possibility to model events with
independent start and end times in `mutwo`.
"""

from .timelines import *
from . import timelines

__all__ = timelines.__all__

# Cleanup
del timelines
