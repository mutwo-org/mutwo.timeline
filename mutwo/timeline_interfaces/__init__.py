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

    :param event: The event to be placed on a :class:`TimeLine`. This needs to
        be an event with a `tag` property. The tag is necessary to concatenate
        two events on a `TimeLine` which belong to the same object (e.g.
        same instrument or same player).
    :type event: core_events.TaggedSimpleEvent | core_events.TaggedSequentialEvent | core_events.SimultaneousEvent
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
        event: core_events.TaggedSimpleEvent
        | core_events.TaggedSequentialEvent
        | core_events.SimultaneousEvent,
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
    :param prohibit_overlaps: If set to ``True`` the :class:`TimeLine`
        will prohibit any action which creates overlapping
        :class:`EventPlacement` with the same tag. Default to ``True``.
    :type prohibit_overlaps: bool

    **Warning:**

    An :class:`TimeLine` itself is not an event and can't be treated
    like an event.
    """

    MinStartTime: typing.TypeAlias = "Time"
    TimeRange: typing.TypeAlias = ranges.Range
    # In this way we can easily and very fast register
    # new EventPlacements.
    EventContainer: typing.TypeAlias = tuple[
        list[MinStartTime], list[TimeRange], list[EventPlacement]
    ]

    def __init__(
        self,
        duration: typing.Optional[UnspecificTime] = None,
        prohibit_overlaps: bool = True,
        *args,
        **kwargs,
    ):

        self._dynamic_duration = duration is None
        self._duration = duration
        self._tag_to_event_container: dict[str, TimeLine.EventContainer] = {}
        self._prohibit_overlaps = prohibit_overlaps

    # ###################################################################### #
    #                          public properties                             #
    # ###################################################################### #

    @property
    def duration(self) -> core_parameters.abc.Duration:
        if self._dynamic_duration:
            try:
                return max(
                    [
                        event_container[1][-1].end
                        for event_container in self._tag_to_event_container.values()
                    ]
                )
            # If there isn't any registered EventPlacement yet.
            except ValueError:
                return 0
        else:
            return self._duration

    @property
    def prohibit_overlaps(self) -> bool:
        return self._prohibit_overlaps

    # ###################################################################### #
    #                          public methods                                #
    # ###################################################################### #

    def register(self, event_placement: EventPlacement):
        """Register a new :class:`EventPlacement` on given :class:`TimeLine`.

        :param event_placement: The :class:`EventPlacement` which should be
            placed on the :class:`TimeLine`.
        :type event_placement: EventPlacement

        When registering an `EventPlacement`, a copy of the `EventPlacement`
        is saved. The registered `EventPlacement` will only be changeable by
        methods provided by :class:`TimeLine`. In this way, :class:`TimeLine`
        can internally easily and in an performant way register new
        :class:`EventPlacement`s and check if any :class:`EventPlacement`
        is overlapping with any already defined one.
        """
        event_placement = event_placement.copy()
        tag = event_placement.event.tag
        time_range = event_placement.time_range
        start = time_range.start

        if not self._dynamic_duration:
            if time_range.end > (duration := self.duration):
                raise timeline_utilities.ExceedDurationError(event_placement, duration)

        try:
            (
                start_list,
                time_range_list,
                event_placement_list,
            ) = self._tag_to_event_container[tag]
        except KeyError:
            self._tag_to_event_container.update(
                {tag: ([start], [time_range], [event_placement])}
            )
            return

        insert_index = bisect.bisect_left(start_list, start)

        try:
            event_placement_after = event_placement_list[insert_index]
        except IndexError:
            event_placement_after = None

        if self.prohibit_overlaps:
            before_insert_index = insert_index - 1
            event_placement_to_compare_list = (
                [event_placement_list[before_insert_index]]
                if before_insert_index >= 0
                else []
            )
            if event_placement_after is not None:
                event_placement_to_compare_list.append(event_placement_after)
            for event_placement_to_compare in event_placement_to_compare_list:
                if event_placement.is_overlapping(event_placement_to_compare):
                    raise timeline_utilities.OverlappingEventPlacementError(
                        event_placement, event_placement_to_compare
                    )

        # If both EventPlacement are at the same time,
        # we will move the EventPlacement with the later end
        # time to the second position.
        if (
            event_placement_after is not None
            and start_list[insert_index] == start
            and time_range.end > time_range_list[insert_index].end
        ):
            insert_index += 1

        start_list.insert(insert_index, start)
        time_range_list.insert(insert_index, time_range)
        event_placement_list.insert(insert_index, event_placement)

    def fetch_tag_to_event_placement_dict(
        self,
    ) -> dict[str, tuple[EventPlacement, ...]]:
        """Fetch a tag -> tuple[event_placement, ...] dict.

        **Warning:**

        The returned :class:`EventPlacement`s are copies of the
        internal :class:`EventPlacement`s of the :class:`TimeLine`.
        In this way the :class:`TimeLine` can ensure internal consistency.
        This means that `fetch_tag_to_event_placement_dict` is
        an expensive operation, because it needs to copy all
        :class:`EventPlacement`. It also means that any changes
        on the returned objects won't affect any objects
        inside the :class:`TimeLine`.
        """

        return {
            tag: tuple(event_placement.copy() for event_placement in event_container[2])
            for tag, event_container in self._tag_to_event_container.items()
        }
