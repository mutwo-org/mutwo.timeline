"""Convert :class:`mutwo.timeline_interfaces.TimeLine` to objects useable by other parts of `mutwo`."""

import typing

import numpy as np
import ranges

from mutwo import core_converters
from mutwo import core_events
from mutwo import core_parameters
from mutwo import timeline_interfaces

__all__ = ("TimeLineToEventPlacementDict", "TimeLineToSimultaneousEvent")

Tag: typing.TypeAlias = "str"


class TimeLineToEventPlacementDict(core_converters.abc.Converter):
    def convert(
        self, timeline_to_convert: timeline_interfaces.TimeLine
    ) -> dict[Tag, tuple[timeline_interfaces.EventPlacement, ...]]:
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
        sequential_event_to_add_count = len(event_to_append) - len(simultaneous_event)
        if sequential_event_to_add_count > 0:
            sequential_event_list = [
                core_events.SequentialEvent([])
                for _ in range(sequential_event_to_add_count)
            ]
            simultaneous_event.extend(sequential_event_list)

        for sequential_event in simultaneous_event:
            sequential_event_duration = sequential_event.duration
            rest_duration = start - sequential_event_duration
            if rest_duration > 0:
                sequential_event.append(core_events.SimpleEvent(rest_duration))

        event_to_append_duration = event_to_append.duration

        for sequential_event_to_append_to, sequential_event_to_append in zip(
            simultaneous_event, event_to_append
        ):
            assert isinstance(
                sequential_event_to_append, core_events.SequentialEvent
            ), "Invalid event structure: Expected SequentialEvent"
            for simple_event_to_append in sequential_event_to_append:
                assert isinstance(
                    simple_event_to_append, core_events.SimpleEvent
                ), "Invalid event structure: Expected SimpleEvent"
                sequential_event_to_append_to.append(simple_event_to_append)

            duration_difference = (
                event_to_append_duration - sequential_event_to_append.duration
            )
            if duration_difference > 0:
                sequential_event_to_append_to.append(
                    core_events.SimpleEvent(duration_difference)
                )

    def _add_tagged_event_to_simultaneous_event(
        self,
        start: core_parameters.abc.Duration,
        end: core_parameters.abc.Duration,
        simultaneous_event: core_events.TaggedSimultaneousEvent,
        tagged_event: core_events.TaggedSimpleEvent
        | core_events.TaggedSequentialEvent
        | core_events.TaggedSimultaneousEvent,
    ):
        event_duration = end - start
        tagged_event = tagged_event.set("duration", event_duration, mutate=False)
        if isinstance(tagged_event, core_events.SimpleEvent):
            tagged_event = core_events.SimultaneousEvent(
                [core_events.SequentialEvent([tagged_event])]
            )
        elif isinstance(tagged_event, core_events.SequentialEvent):
            tagged_event = core_events.SimultaneousEvent([tagged_event])
        self._append_to_simultaneous_event(start, simultaneous_event, tagged_event)

    def _fill_with_rest_until_duration(
        self,
        duration: core_parameters.abc.Duration,
        tagged_simultaneous_event_iterable: typing.Iterable[
            core_events.TaggedSimultaneousEvent
        ],
    ):
        for simultaneous_event in tagged_simultaneous_event_iterable:
            for sequential_event in simultaneous_event:
                difference = duration - sequential_event.duration
                if difference > 0:
                    sequential_event.append(core_events.SimpleEvent(difference))

    def convert(
        self, timeline_to_convert: timeline_interfaces.TimeLine
    ) -> core_events.SimultaneousEvent[
        core_events.TaggedSimultaneousEvent[
            core_events.SequentialEvent[core_events.SimpleEvent]
        ]
    ]:
        duration = timeline_to_convert.duration
        tag_set = timeline_to_convert.tag_set

        tag_to_tagged_simultaneous_event = {
            tag: core_events.TaggedSimultaneousEvent([], tag=tag) for tag in tag_set
        }

        timeline_to_convert.sort()
        for event_placement in timeline_to_convert.event_placement_tuple:
            start, end = self._event_placement_to_start_and_end(event_placement)
            for tagged_event in event_placement.event:
                tag = tagged_event.tag
                self._add_tagged_event_to_simultaneous_event(
                    start,
                    end,
                    tag_to_tagged_simultaneous_event[tag],
                    tagged_event,
                )

        if duration is not None:
            self._fill_with_rest_until_duration(
                duration, tag_to_tagged_simultaneous_event.values()
            )

        return core_events.SimultaneousEvent(
            tuple(tag_to_tagged_simultaneous_event.values())
        )
