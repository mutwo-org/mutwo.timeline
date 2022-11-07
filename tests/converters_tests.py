import unittest

import ranges
import quicktions as fractions

from mutwo import core_events
from mutwo import timeline_converters
from mutwo import timeline_interfaces


class TimeLineToEventPlacementDictTest(unittest.TestCase):
    def setUp(self):
        self.tag0, self.tag1 = "ab"
        self.event0, self.event1 = (
            core_events.TaggedSimpleEvent(1, tag=tag) for tag in (self.tag0, self.tag1)
        )
        self.simultaneous_event_0 = core_events.SimultaneousEvent([self.event0])
        self.simultaneous_event_1 = core_events.SimultaneousEvent([self.event1])
        self.simultaneous_event_01 = core_events.SimultaneousEvent(
            [self.event0, self.event1]
        )
        self.event_placement_list = [
            timeline_interfaces.EventPlacement(self.simultaneous_event_0, 0, 1),
            timeline_interfaces.EventPlacement(self.simultaneous_event_1, 0, 2),
            timeline_interfaces.EventPlacement(self.simultaneous_event_01, 4, 6),
            timeline_interfaces.EventPlacement(self.simultaneous_event_1, 10, 11),
        ]
        self.timeline = timeline_interfaces.TimeLine(self.event_placement_list)
        self.timeline_to_event_placement_dict = (
            timeline_converters.TimeLineToEventPlacementDict()
        )

    def test_convert(self):
        tag_to_event_placement_tuple = self.timeline_to_event_placement_dict.convert(
            self.timeline
        )
        expected_tag_to_event_placement_tuple = {
            self.tag0: (self.event_placement_list[0], self.event_placement_list[2]),
            self.tag1: (
                self.event_placement_list[1],
                self.event_placement_list[2],
                self.event_placement_list[3],
            ),
        }
        self.assertEqual(
            tag_to_event_placement_tuple, expected_tag_to_event_placement_tuple
        )


class TimeLineToSimultaneousEventTest(unittest.TestCase):
    def setUp(self):
        self.timeline_to_simultaneous_event = (
            timeline_converters.TimeLineToSimultaneousEvent()
        )
        self.simple_event_a = core_events.TaggedSimpleEvent(1, tag="a")
        self.simple_event_b = core_events.TaggedSimpleEvent(1, tag="b")
        self.simultaneous_event_a = core_events.TaggedSimultaneousEvent(
            [
                core_events.SequentialEvent(
                    [self.simple_event_a.copy(), self.simple_event_a.copy()]
                ),
                core_events.SequentialEvent(
                    [self.simple_event_a.copy(), self.simple_event_a.copy()]
                ),
            ],
            tag="a",
        )
        self.timeline = timeline_interfaces.TimeLine(
            [
                timeline_interfaces.EventPlacement(
                    core_events.SimultaneousEvent([self.simple_event_a]), 0, 1
                ),
                timeline_interfaces.EventPlacement(
                    core_events.SimultaneousEvent([self.simple_event_a]), 2, 3
                ),
                timeline_interfaces.EventPlacement(
                    core_events.SimultaneousEvent([self.simple_event_b]),
                    1,
                    ranges.Range(4, 6),
                ),
                timeline_interfaces.EventPlacement(
                    core_events.SimultaneousEvent([self.simultaneous_event_a]), 9, 11
                ),
            ]
        )

    def test_convert(self):
        simultaneous_event = self.timeline_to_simultaneous_event.convert(self.timeline)

        self.assertEqual(len(simultaneous_event), 2)
        self.assertTrue(simultaneous_event[0].tag, self.simple_event_a.tag)
        self.assertTrue(simultaneous_event[1].tag, self.simple_event_b.tag)
        self.assertEqual(len(simultaneous_event[0]), 2)
        self.assertEqual(len(simultaneous_event[0][0]), 6)
        self.assertEqual(len(simultaneous_event[0][1]), 3)
        self.assertEqual(len(simultaneous_event[1][0]), 3)
        self.assertEqual(simultaneous_event[0].duration, simultaneous_event[1].duration)
