import typing

import numpy as np
import ranges

from mutwo import core_converters
from mutwo import core_events
from mutwo import core_parameters
from mutwo import timeline_interfaces
from mutwo import timeline_utilities


class EventPlacementTupleToSequentialEvent(core_converters.abc.Converter):
    def __init__(self, random_seed: int = 1000):
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

    def convert(
        self,
        event_placement_tuple: tuple[timeline_interfaces.EventPlacement, ...],
        duration: typing.Optional[core_parameters.abc.Duration | typing.Any] = None,
    ) -> core_events.SequentialEvent:
        duration = core_events.configurations.UNKNOWN_OBJECT_TO_DURATION(duration)

        sequential_event = core_events.SequentialEvent([])
        if event_placement_tuple:
            last_end = None
            for event_placement in event_placement_tuple:
                start, end = self._event_placement_to_start_and_end(event_placement)

                if last_end is None:
                    rest_duration = start
                else:
                    rest_duration = start - last_end

                if rest_duration > 0:
                    sequential_event.append(core_events.SimpleEvent(rest_duration))

                event_duration = end - start
                event = event_placement.event
                sequential_event.append(
                    event.set("duration", event_duration, mutate=False)
                )

                last_end = end

        if duration is not None:
            difference = duration - sequential_event.duration
            if difference > 0:
                sequential_event.append(core_events.SimpleEvent(difference))

        return sequential_event


class TimeLineToSimultaneousEvent(core_converters.abc.Converter):
    def __init__(self, random_seed: int = 1000):
        self._event_placement_tuple_to_sequential_event = (
            EventPlacementTupleToSequentialEvent(random_seed)
        )

    def convert(
        self, timeline_to_convert: timeline_interfaces.TimeLine
    ) -> core_events.SimultaneousEvent[core_events.TaggedSequentialEvent]:
        duration = timeline_to_convert.duration
        tag_to_event_placement_tuple_dict = (
            timeline_to_convert.fetch_tag_to_event_placement_dict()
        )
        simultaneous_event = core_events.SimultaneousEvent([])
        for tag, event_placement_tuple in tag_to_event_placement_tuple_dict.items():
            sequential_event = self._event_placement_tuple_to_sequential_event(
                event_placement_tuple, duration
            )
            tagged_sequential_event = core_events.TaggedSequentialEvent(
                sequential_event[:], tag=tag
            )
            simultaneous_event.append(tagged_sequential_event)
        return simultaneous_event
