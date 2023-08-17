import typing

import numpy as np
import ranges

from mutwo import core_converters
from mutwo import core_events
from mutwo import core_parameters
from mutwo import core_utilities
from mutwo import timeline_interfaces

__all__ = (
    "TimeLineToEventPlacementDict",
    "TimeLineToSimultaneousEvent",
    "TimeLineToEventPlacementTuple",
    "EventPlacementTupleToGaplessEventPlacementTuple",
    "EventPlacementTupleToSplitEventPlacementDict",
)

Tag: typing.TypeAlias = "str"


class TimeLineToEventPlacementDict(core_converters.abc.Converter):
    def convert(
        self, timeline_to_convert: timeline_interfaces.TimeLine
    ) -> dict[Tag, tuple[timeline_interfaces.EventPlacement, ...]]:
        timeline_to_convert.sort()
        tag_to_event_placement_list = {tag: [] for tag in timeline_to_convert.tag_set}
        for event_placement in timeline_to_convert.event_placement_tuple:
            for tag in event_placement.tag_tuple:
                # TODO(Add checks for overlaps!)
                tag_to_event_placement_list[tag].append(event_placement)
        return {
            tag: tuple(event_placement_list)
            for tag, event_placement_list in tag_to_event_placement_list.items()
        }


class TimeLineToSimultaneousEvent(core_converters.abc.Converter):
    """Create event with SimultaneousEvent for each tag.

    :param random_seed: Seed for random operation in case
        `start_or_start_range` or `end_or_end_range` of an
        :class:`mutwo.timeline_interfaces.EventPlacement` is a
        `ranges.Range` and :class:`TimeLineToSimultaneousEvent`
        needs to pick a value within the given range.
    :type random_seed: int

    The main intention of this converter is to convert a
    :class:`TimeLine` into a representation which is useable
    for concrete third party converters like
    :class:`mutwo.midi_converters.EventToMidiFile`.

    To be successful the tagged events in the
    :class:`mutwo.timeline_interfaces.EventPlacement` in the
    :class:`mutwo.timeline_interfaces.TimeLine` which is
    converted need a specific structure: the deepest nested
    structure they can follow is:

        core_events.SimultaneousEvent[
            core_events.SequentialEvent[
                core_events.SimpleEvent
            ]
        ]

    Because this will be the final structure. This clean
    ordering is necessary to be functional with various third
    party converters as e.g.
    :class:`mutwo.midi_converters.EventToMidiFile`.
    """

    def __init__(self, random_seed: int = 100):
        self._random = np.random.default_rng(random_seed)

    def _time_or_time_range_to_time(
        self, time_or_time_range: ranges.Range | core_parameters.abc.Duration
    ) -> core_parameters.abc.Duration:
        if isinstance(time_or_time_range, ranges.Range):
            return core_parameters.DirectDuration(
                self._random.uniform(
                    float(time_or_time_range.start), float(time_or_time_range.end)
                )
            )
        return time_or_time_range

    def _event_placement_to_start_and_end(
        self, event_placement: timeline_interfaces.EventPlacement
    ) -> tuple[core_parameters.abc.Duration, core_parameters.abc.Duration]:
        return (
            self._time_or_time_range_to_time(event_placement.start_or_start_range),
            self._time_or_time_range_to_time(event_placement.end_or_end_range),
        )

    def _append_to_simultaneous_event(
        self,
        start: core_parameters.abc.Duration,
        simultaneous_event: core_events.TaggedSimultaneousEvent,
        event_to_append: core_events.SimultaneousEvent[
            core_events.SequentialEvent[core_events.SimpleEvent]
        ],
    ):
        if start > (simultaneous_event_duration := simultaneous_event.duration):
            # In case our simultaneous event is still empty, 'extend_until'
            # will do nothing (because it only extends sequential events,
            # but ignores simultaneous events). Therefore we need to explicitly
            # add a sequential event before extending.
            if not simultaneous_event:
                simultaneous_event.append(core_events.SequentialEvent([]))
            simultaneous_event.extend_until(start)
        # We have an overlap
        elif start < simultaneous_event_duration:
            # TODO(We need to check for overlaps. If we find overlaps:
            #       (a) with prohibit flag
            #       (b) with allow flag
            #
            #       (a) raise Exception
            #       (b) check for all other SequentialEvents,
            #           how many are they where we don't have
            #           any conflicts? Where are they? (save in list)
            #           If there aren't enough, add new sequential events.
            #           Then: only append to the sequential events without
            #           conflicts.
            # elif rest_duration < 0
            raise NotImplementedError("Overlap handler isn't implemented yet!")

        try:
            simultaneous_event.concatenate_by_tag(event_to_append)
        except core_utilities.NoTagError:
            simultaneous_event.concatenate_by_index(event_to_append)

    def _add_tagged_event_to_simultaneous_event(
        self,
        start: core_parameters.abc.Duration,
        simultaneous_event: core_events.TaggedSimultaneousEvent,
        tagged_event: core_events.TaggedSimpleEvent
        | core_events.TaggedSequentialEvent
        | core_events.TaggedSimultaneousEvent,
    ):
        if isinstance(tagged_event, core_events.SimpleEvent):
            tagged_event = core_events.SimultaneousEvent(
                [core_events.SequentialEvent([tagged_event])]
            )
        elif isinstance(tagged_event, core_events.SequentialEvent):
            tagged_event = core_events.SimultaneousEvent([tagged_event])
        self._append_to_simultaneous_event(start, simultaneous_event, tagged_event)

    def _event_placement_to_event(
        self,
        event_placement: timeline_interfaces.EventPlacement,
        start: core_parameters.abc.Duration,
        end: core_parameters.abc.Duration,
    ) -> typing.Optional[core_events.SimultaneousEvent]:
        event_duration = end - start
        try:
            return event_placement.event.set("duration", event_duration, mutate=False)
        except core_utilities.CannotSetDurationOfEmptyComplexEvent:
            return None

    def convert(
        self, timeline_to_convert: timeline_interfaces.TimeLine
    ) -> core_events.SimultaneousEvent[
        core_events.TaggedSimultaneousEvent[
            core_events.SequentialEvent[core_events.SimpleEvent]
        ]
    ]:
        duration = timeline_to_convert.duration
        tag_tuple = tuple(sorted(timeline_to_convert.tag_set))

        tag_to_tagged_simultaneous_event = {
            tag: core_events.TaggedSimultaneousEvent([], tag=tag) for tag in tag_tuple
        }

        timeline_to_convert.sort()
        for event_placement in timeline_to_convert.event_placement_tuple:
            start, end = self._event_placement_to_start_and_end(event_placement)
            # If the event of our event placement doesn't have any children,
            # this is `None` and we just need to ignore it.
            if not (
                event := self._event_placement_to_event(event_placement, start, end)
            ):
                continue
            for tagged_event in event:
                tag = tagged_event.tag
                self._add_tagged_event_to_simultaneous_event(
                    start,
                    tag_to_tagged_simultaneous_event[tag],
                    tagged_event,
                )

        duration = duration or max(
            (e.duration for e in tag_to_tagged_simultaneous_event.values())
        )
        [e.extend_until(duration) for e in tag_to_tagged_simultaneous_event.values()]

        return core_events.SimultaneousEvent(
            tuple(tag_to_tagged_simultaneous_event.values())
        )


class TimeLineToEventPlacementTuple(core_converters.abc.Converter):
    """Fetch from :class:`~mutwo.timeline_interfaces.TimeLine` all :class:`~mutwo.timeline_interfaces.EventPlacement` which contains of user defined tags.

    Unlike :class:`TimeLineToEventPlacementDict` this converter
    doesn't split the fetched :class:`mutwo.timeline_interfaces.EventPlacement`s
    into different `tuples`, but returns all of them in one common `tuple`.
    """

    def convert(
        self,
        timeline_to_convert: timeline_interfaces.TimeLine,
        tag_tuple: tuple[Tag, ...],
    ) -> tuple[timeline_interfaces.EventPlacement, ...]:
        timeline_to_convert.sort()

        # XXX: Should we add any checks for overlaps?
        event_placement_list: list[timeline_interfaces.EventPlacement] = []
        for event_placement in timeline_to_convert.event_placement_tuple:
            if any([tag in tag_tuple for tag in event_placement.tag_tuple]):
                event_placement_list.append(event_placement.copy())

        return tuple(event_placement_list)


class EventPlacementTupleToSplitEventPlacementDict(core_converters.abc.Converter):
    """Split :class:`~mutwo.timeline_interfaces.EventPlacement` into new `EventPlacement`s by tags.

    So the returned `event` attribute of each returned
    :class:`mutwo.timeline_interfaces.EventPlacement` only
    contains one specific tagged event.
    """

    def convert(
        self,
        event_placement_tuple_to_convert: tuple[
            timeline_interfaces.EventPlacement, ...
        ],
    ) -> dict[Tag, tuple[timeline_interfaces.EventPlacement, ...]]:
        tag_to_event_placement_list: dict[
            str, list[timeline_interfaces.EventPlacement]
        ] = {}
        for event_placement in event_placement_tuple_to_convert:
            for event_index, event in enumerate(event_placement.event):
                try:
                    event_placement_list = tag_to_event_placement_list[event.tag]
                except KeyError:
                    event_placement_list = []
                    tag_to_event_placement_list.update(
                        {event.tag: event_placement_list}
                    )
                new_event_placement = event_placement.copy()
                new_event_placement.event = core_events.SimultaneousEvent(
                    [new_event_placement.event[event_index]]
                )
                event_placement_list.append(new_event_placement)
        return {
            tag: tuple(event_placement_list)
            for tag, event_placement_list in tag_to_event_placement_list.items()
        }


class EventPlacementTupleToGaplessEventPlacementTuple(core_converters.abc.Converter):
    """Fill empty :class:`~mutwo.timeline_interfaces.EventPlacement` into the gaps between two `EventPlacement`."""

    def convert(
        self,
        event_placement_tuple_to_convert: tuple[
            timeline_interfaces.EventPlacement, ...
        ],
        duration: typing.Optional[core_parameters.abc.Duration] = None,
    ) -> tuple[timeline_interfaces.EventPlacement, ...]:
        def add_rest(
            start: core_parameters.abc.Duration, end: core_parameters.abc.Duration
        ):
            new_event_placement_list.append(
                timeline_interfaces.EventPlacement(
                    core_events.SimultaneousEvent(
                        [core_events.TaggedSimpleEvent(0, tag=tag)]
                    ),
                    start,
                    end,
                )
            )

        event_placement_list = sorted(
            event_placement_tuple_to_convert,
            key=lambda event_placement: (
                event_placement.min_start,
                event_placement.max_end,
            ),
        )

        new_event_placement_list = []
        last_end = 0
        tag = None
        for event_placement in event_placement_list:
            if tag is None:
                tag = event_placement.event[0].tag
            start, end = event_placement.min_start, event_placement.max_end
            if start > last_end:
                add_rest(last_end, start)
            new_event_placement_list.append(event_placement.copy())
            last_end = end

        if duration is not None and last_end < duration:
            add_rest(last_end, duration)

        return tuple(new_event_placement_list)
