import unittest

import ranges
import quicktions as fractions

from mutwo import core_events
from mutwo import timeline_converters
from mutwo import timeline_interfaces


class EventPlacementTupleToSequentialEventTest(unittest.TestCase):
    def setUp(self):
        self.event_placement_tuple_to_sequential_event = (
            timeline_converters.EventPlacementTupleToSequentialEvent()
        )

    def test_convert(self):
        event = core_events.TaggedSimpleEvent(1, tag="test")
        rest = core_events.SimpleEvent(1)
        event_placement_tuple = (
            timeline_interfaces.EventPlacement(event, 1, 3),
            timeline_interfaces.EventPlacement(event, 3, 4),
            timeline_interfaces.EventPlacement(event, ranges.Range(5.5, 6), 7),
        )
        duration = 10

        sequential_event = self.event_placement_tuple_to_sequential_event.convert(
            event_placement_tuple, duration
        )

        expected_sequential_event = core_events.SequentialEvent(
            [
                rest,
                event.set("duration", 2, mutate=False),
                event,
                rest.set(
                    "duration",
                    # XXX: Will change if seed changes or DirectDuration
                    # parses in different way (e.g. only allows more simple
                    # fractions).
                    fractions.Fraction(991181968585767, 562949953421312),
                    mutate=False,
                ),
                event.set(
                    "duration",
                    fractions.Fraction(697667891678169, 562949953421312),
                    mutate=False,
                ),
                rest.set("duration", 3, mutate=False),
            ]
        )

        self.assertEqual(sequential_event, expected_sequential_event)


class TimeLineToSimultaneousEventTest(unittest.TestCase):
    def setUp(self):
        self.timeline_to_simultaneous_event = (
            timeline_converters.TimeLineToSimultaneousEvent()
        )
        self.timeline = timeline_interfaces.TimeLine()

        self.event_a = core_events.TaggedSimpleEvent(1, tag="a")
        self.event_b = core_events.TaggedSimpleEvent(1, tag="b")
        self.timeline.register(timeline_interfaces.EventPlacement(self.event_a, 0, 1))
        self.timeline.register(timeline_interfaces.EventPlacement(self.event_a, 2, 3))
        self.timeline.register(
            timeline_interfaces.EventPlacement(self.event_b, 1, ranges.Range(4, 6))
        )

    def test_convert(self):
        simultaneous_event = self.timeline_to_simultaneous_event.convert(self.timeline)

        self.assertEqual(len(simultaneous_event), 2)
        self.assertTrue(simultaneous_event[0].tag, self.event_a.tag)
        self.assertTrue(simultaneous_event[1].tag, self.event_b.tag)
        self.assertEqual(len(simultaneous_event[0]), 4)
        # XXX: Has 3 events, because the maximum duration is higher
        # than the actual picked duration.
        self.assertEqual(len(simultaneous_event[1]), 3)
        self.assertEqual(simultaneous_event[0].duration, simultaneous_event[1].duration)
