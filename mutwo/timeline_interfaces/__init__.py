"""Place events with absolute start and end times on a time line.

`Mutwo` events usually follow an approach of relative placement in time.
This means each event has a duration, and if there is a sequence of events
the second event will start after the first event finishes. So the start
and end time of any event dependent on all events which happens before the
given event. This package implements the possibility to model events with
independent start and end times in `mutwo`.
"""

from __future__ import annotations

import bisect
import copy
import statistics
import typing

import ranges

from mutwo import core_events
from mutwo import core_parameters
from mutwo import core_utilities
from mutwo import timeline_utilities

UnspecificTime: typing.TypeAlias = "core_parameters.abc.Duration | typing.Any"
UnspecificTimeOrTimeRange: typing.TypeAlias = "UnspecificTime | ranges.Range"
TimeOrTimeRange: typing.TypeAlias = "core_parameters.abc.Duration | ranges.Range"

__all__ = ("EventPlacement", "TimeLine")


class EventPlacement(object):
    """Place any event at specific start and end times.

    :param event: The event to be placed on a :class:`TimeLine`.
        This needs to be filled with events with a `tag` property. Each
        child event represents a specific object (e.g. instrument or
        player) The tag is necessary to concatenate two events on a
        `TimeLine` which belong to the same object (e.g. same instrument
        or same player).
    :type event: core_events.SimultaneousEvent[core_events.TaggedSimpleEvent | core_events.TaggedSequentialEvent | core_events.SimultaneousEvent]
    :param start_or_start_range: Sets when the event starts. This can
        be a single :class:`mutwo.core_parameters.abc.Duration` or a
        :class:`ranges.Range` of two durations. In the second case
        the placement is flexible within the given area.
    :type start_or_start_range: UnspecificTimeOrTimeRange
    :param end_or_end_range: Sets when the event ends. This can
        be a single :class:`mutwo.core_parameters.abc.Duration` or a
        :class:`ranges.Range` of two durations. In the second case
        the placement is flexible within the given area.
    :type end_or_end_range: UnspecificTimeOrTimeRange

    **Warning:**

    An :class:`EventPlacement` itself is not an event and can't be treated
    like an event.
    """

    def __init__(
        self,
        event: core_events.SimultaneousEvent[
            core_events.TaggedSimpleEvent
            | core_events.TaggedSequentialEvent
            | core_events.SimultaneousEvent
        ],
        start_or_start_range: UnspecificTimeOrTimeRange,
        end_or_end_range: UnspecificTimeOrTimeRange,
    ):
        self.start_or_start_range = start_or_start_range
        self.end_or_end_range = end_or_end_range
        self.event = event

    # ###################################################################### #
    #                       private static methods                           #
    # ###################################################################### #

    @staticmethod
    def _unspecified_to_specified_time_or_time_range(
        unspecified_time_or_time_range: UnspecificTimeOrTimeRange,
    ) -> TimeOrTimeRange:
        # Ensure we get ranges filled with Duration objects or single
        # duration objects.
        if isinstance(unspecified_time_or_time_range, ranges.Range):
            return ranges.Range(
                *tuple(
                    core_events.configurations.UNKNOWN_OBJECT_TO_DURATION(
                        unknown_object
                    )
                    for unknown_object in (
                        unspecified_time_or_time_range.start,
                        unspecified_time_or_time_range.end,
                    )
                )
            )
        else:
            return core_events.configurations.UNKNOWN_OBJECT_TO_DURATION(
                unspecified_time_or_time_range
            )

    @staticmethod
    def _get_mean_of_time_or_time_range(
        time_or_time_range: TimeOrTimeRange,
    ) -> core_parameters.abc.Duration:
        if isinstance(time_or_time_range, ranges.Range):
            return core_parameters.DirectDuration(
                statistics.mean(
                    (time_or_time_range.start.duration, time_or_time_range.end.duration)
                )
            )
        else:
            return time_or_time_range

    @staticmethod
    def _get_extrema_of_time_or_time_range(
        time_or_time_range: TimeOrTimeRange,
        operation: typing.Callable[[typing.Sequence], core_parameters.abc.Duration],
    ):
        if isinstance(time_or_time_range, ranges.Range):
            return operation((time_or_time_range.start, time_or_time_range.end))
        else:
            return time_or_time_range

    @staticmethod
    def _move_time_or_time_range(
        time_or_time_range: TimeOrTimeRange, duration: core_parameters.abc.Duration
    ) -> TimeOrTimeRange:
        if isinstance(time_or_time_range, ranges.Range):
            time_or_time_range.start += duration
            time_or_time_range.end += duration
            return time_or_time_range
        else:
            return time_or_time_range + duration

    # ###################################################################### #
    #                          magic methods                                 #
    # ###################################################################### #

    def __eq__(self, other: typing.Any) -> bool:
        return core_utilities.test_if_objects_are_equal_by_parameter_tuple(
            self, other, ("event", "start_or_start_range", "end_or_end_range")
        )

    def __str__(self) -> str:
        return (
            f"{type(self).__name__}(event = '{self.event}', "
            f"start_or_start_range = '{self.start_or_start_range}', "
            f"end_or_end_range = '{self.end_or_end_range}'"
        )

    # ###################################################################### #
    #                          public properties                             #
    # ###################################################################### #

    @property
    def tag_tuple(self) -> tuple[str, ...]:
        return tuple(event.tag for event in self.event)

    @property
    def start_or_start_range(self) -> TimeOrTimeRange:
        return self._start_or_start_range

    @start_or_start_range.setter
    def start_or_start_range(self, start_or_start_range: UnspecificTimeOrTimeRange):
        self._start_or_start_range = (
            EventPlacement._unspecified_to_specified_time_or_time_range(
                start_or_start_range
            )
        )

    @property
    def end_or_end_range(self) -> TimeOrTimeRange:
        return self._end_or_end_range

    @end_or_end_range.setter
    def end_or_end_range(self, end_or_end_range: UnspecificTimeOrTimeRange):
        self._end_or_end_range = (
            EventPlacement._unspecified_to_specified_time_or_time_range(
                end_or_end_range
            )
        )

    @property
    def duration(self) -> core_parameters.abc.Duration:
        return self.max_end - self.min_start

    @property
    def mean_start(self) -> core_parameters.abc.Duration:
        return EventPlacement._get_mean_of_time_or_time_range(self.start_or_start_range)

    @property
    def mean_end(self) -> core_parameters.abc.Duration:
        return EventPlacement._get_mean_of_time_or_time_range(self.end_or_end_range)

    @property
    def min_start(self) -> core_parameters.abc.Duration:
        return EventPlacement._get_extrema_of_time_or_time_range(
            self.start_or_start_range, min
        )

    @property
    def max_start(self) -> core_parameters.abc.Duration:
        return EventPlacement._get_extrema_of_time_or_time_range(
            self.start_or_start_range, max
        )

    @property
    def min_end(self) -> core_parameters.abc.Duration:
        return EventPlacement._get_extrema_of_time_or_time_range(
            self.end_or_end_range, min
        )

    @property
    def max_end(self) -> core_parameters.abc.Duration:
        return EventPlacement._get_extrema_of_time_or_time_range(
            self.end_or_end_range, max
        )

    @property
    def time_range(self) -> ranges.Range:
        return ranges.Range(self.min_start, self.max_end)

    # ###################################################################### #
    #                          public methods                                #
    # ###################################################################### #

    def is_overlapping(self, other: EventPlacement) -> bool:
        return not self.time_range.isdisjoint(other.time_range)

    @core_utilities.add_copy_option
    def move_by(self, duration: UnspecificTime) -> EventPlacement:
        duration = core_events.configurations.UNKNOWN_OBJECT_TO_DURATION(duration)
        self.start_or_start_range, self.end_or_end_range = (
            EventPlacement._move_time_or_time_range(time_or_time_range, duration)
            for time_or_time_range in (self.start_or_start_range, self.end_or_end_range)
        )
        return self

    def copy(self) -> EventPlacement:
        return type(self)(
            self.event.copy(),
            copy.copy(self.start_or_start_range),
            copy.copy(self.end_or_end_range),
        )


# TODO(Add conflict solution hook to prevent overlaps!)
class TimeLine(object):
    """Timeline to place events on.

    :param duration: If this is set to `None` the ``duration``
        property of the `TimeLine` is dynamically calculated
        (by the end times of all registered :class:`EventPlacement`.
        If the duration is not `None`, then the duration is statically
        set to this time. If the user tries to register an
        :class:`EventPlacement` with end > duration this would raise
        an error. Default to ``None``.
    :type duration: typing.Optional[UnspecificTime]

    **Warning:**

    An :class:`TimeLine` itself is not an event and can't be treated
    like an event.
    """

    def __init__(
        self,
        event_placement_sequence: typing.Sequence[EventPlacement] = [],
        duration: typing.Optional[UnspecificTime] = None,
    ):

        self._dynamic_duration = duration is None
        self._duration = duration
        self._event_placement_list: list[EventPlacement] = list(
            event_placement_sequence
        )

    # ###################################################################### #
    #                          public properties                             #
    # ###################################################################### #

    @property
    def duration(self) -> core_parameters.abc.Duration:
        if self._dynamic_duration:
            try:
                return max(
                    [
                        event_placement.max_end
                        for event_placement in self._event_placement_list
                    ]
                )
            # If there isn't any registered EventPlacement yet.
            except ValueError:
                return 0
        else:
            return self._duration

    @property
    def event_placement_tuple(self) -> tuple[EventPlacement, ...]:
        return tuple(self._event_placement_list)

    @property
    def tag_set(self) -> set[str]:
        tag_set = set([])
        for event_placement in self.event_placement_tuple:
            for tag in event_placement.tag_tuple:
                tag_set.add(tag)
        return tag_set

    # ###################################################################### #
    #                          public methods                                #
    # ###################################################################### #

    def register(self, event_placement: EventPlacement):
        """Register a new :class:`EventPlacement` on given :class:`TimeLine`.

        :param event_placement: The :class:`EventPlacement` which should be
            placed on the :class:`TimeLine`.
        :type event_placement: EventPlacement
        """
        end = event_placement.max_end

        # TODO(I think we should move the ExceedDurationError also to
        # follow-up classes (same like OverlapError). Why? This
        # improves performance here. And I'm not sure if a static
        # duration of TimeLine makes sense. On the other hand it
        # makes sense to stretch all outcoming events to the same
        # duration in the end.)
        if not self._dynamic_duration:
            if end > (duration := self.duration):
                raise timeline_utilities.ExceedDurationError(event_placement, duration)

        self._event_placement_list.append(event_placement)

    @core_utilities.add_copy_option
    def sort(self, mutate: bool = True) -> TimeLine:
        """Sort :class:`EventPlacement`s by start time (and if equal by end time)."""

        self._event_placement_list.sort(
            key=lambda event_placement: (
                event_placement.min_start,
                event_placement.max_end,
            )
        )
        return self

    def get_event_placement(
        self, tag: str, index: int, *, sort: bool = True
    ) -> EventPlacement:
        """Find specific :class:`EventPlacement`

        :param tag: The tag which the :class:`EventPlacement` should include.
        :type tag: str
        :param index: The index of the :class:`EventPlacement`
        :type index: int
        :param sort: Can be set to ``False`` when sequentially calling
            `get_event_placement` without changing the :class:`TimeLine`.
            When `sort = False`, but the :class:`TimeLine` (or any
            :class:`EventPlacement` inside the time :class:`TimeLine`
            has changed unexpected results may happen. If you want to be
            sure not to break anything, just leave it as ``True``.
            Default to ``True``.
        :type sort: bool
        """
        if sort:
            self.sort()
        for counter, event_placement in enumerate(
            filter(
                lambda event_placement: tag in event_placement.tag_tuple,
                self.event_placement_tuple,
            )
        ):
            if counter == index:
                return event_placement
        raise timeline_utilities.EventPlacementNotFoundError(tag, index)
