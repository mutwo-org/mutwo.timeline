import unittest

import ranges

from mutwo import core_events
from mutwo import core_parameters
from mutwo import timeline_interfaces
from mutwo import timeline_utilities


class EventPlacementTest(unittest.TestCase):
    def setUp(self):
        self.event_placement_with_start_and_end = timeline_interfaces.EventPlacement(
            core_events.SimultaneousEvent([core_events.TaggedSimpleEvent(1)]), 0, 1
        )

        self.event_placement_with_start_range_and_end_range = (
            timeline_interfaces.EventPlacement(
                core_events.SimultaneousEvent([core_events.TaggedSimpleEvent(1)]),
                ranges.Range(0, 0.5),
                ranges.Range(1, 1.5),
            )
        )

    def test_duration(self):
        self.assertEqual(self.event_placement_with_start_and_end.duration, 1)
        self.assertEqual(
            self.event_placement_with_start_range_and_end_range.duration, 1.5
        )

    def test_mean_start(self):
        self.assertEqual(self.event_placement_with_start_and_end.mean_start, 0)
        self.assertEqual(
            self.event_placement_with_start_range_and_end_range.mean_start, 0.25
        )

    def test_mean_end(self):
        self.assertEqual(self.event_placement_with_start_and_end.mean_end, 1)
        self.assertEqual(
            self.event_placement_with_start_range_and_end_range.mean_end, 1.25
        )

    def test_min_start(self):
        self.assertEqual(self.event_placement_with_start_and_end.min_start, 0)
        self.assertEqual(
            self.event_placement_with_start_range_and_end_range.min_start, 0
        )

    def test_max_start(self):
        self.assertEqual(self.event_placement_with_start_and_end.max_start, 0)
        self.assertEqual(
            self.event_placement_with_start_range_and_end_range.max_start, 0.5
        )

    def test_min_end(self):
        self.assertEqual(self.event_placement_with_start_and_end.min_end, 1)
        self.assertEqual(self.event_placement_with_start_range_and_end_range.min_end, 1)

    def test_max_end(self):
        self.assertEqual(self.event_placement_with_start_and_end.max_end, 1)
        self.assertEqual(
            self.event_placement_with_start_range_and_end_range.max_end, 1.5
        )

    def test_time_range(self):
        self.assertEqual(
            self.event_placement_with_start_and_end.time_range,
            ranges.Range(
                core_parameters.DirectDuration(0), core_parameters.DirectDuration(1)
            ),
        )
        self.assertEqual(
            self.event_placement_with_start_range_and_end_range.time_range,
            ranges.Range(
                core_parameters.DirectDuration(0), core_parameters.DirectDuration(1.5)
            ),
        )

    def test_is_overlapping(self):
        event = core_events.SimultaneousEvent(
            [core_events.TaggedSimpleEvent(1, tag="test")]
        )
        event_placement0 = timeline_interfaces.EventPlacement(event, 1, 2)
        event_placement1 = timeline_interfaces.EventPlacement(event, 0, 3)
        event_placement2 = timeline_interfaces.EventPlacement(
            event, ranges.Range(0.5, 1), ranges.Range(2.5, 4)
        )
        event_placement3 = timeline_interfaces.EventPlacement(event, 10, 12)
        event_placement4 = timeline_interfaces.EventPlacement(
            event, 2, ranges.Range(4, 10)
        )

        self.assertTrue(event_placement0.is_overlapping(event_placement1))
        self.assertTrue(event_placement1.is_overlapping(event_placement0))

        self.assertTrue(event_placement0.is_overlapping(event_placement2))
        self.assertFalse(event_placement0.is_overlapping(event_placement3))
        self.assertFalse(event_placement0.is_overlapping(event_placement4))

        self.assertTrue(event_placement1.is_overlapping(event_placement2))
        self.assertFalse(event_placement1.is_overlapping(event_placement3))
        self.assertTrue(event_placement1.is_overlapping(event_placement4))

        self.assertFalse(event_placement2.is_overlapping(event_placement3))
        self.assertTrue(event_placement2.is_overlapping(event_placement4))

        self.assertFalse(event_placement3.is_overlapping(event_placement4))

    def test_move_by(self):
        self.assertEqual(
            self.event_placement_with_start_and_end.move_by(1, mutate=False),
            timeline_interfaces.EventPlacement(
                self.event_placement_with_start_and_end.event, 1, 2
            ),
        )
        self.assertEqual(
            self.event_placement_with_start_range_and_end_range.move_by(
                1, mutate=False
            ),
            timeline_interfaces.EventPlacement(
                self.event_placement_with_start_and_end.event,
                ranges.Range(1, 1.5),
                ranges.Range(2, 2.5),
            ),
        )

    def test_copy(self):
        event_placement = self.event_placement_with_start_and_end
        event_placement_copy = event_placement.copy()

        self.assertEqual(event_placement, event_placement_copy)

        event_placement_copy.start_or_start_range = 0.5

        self.assertNotEqual(
            event_placement_copy.start_or_start_range,
            event_placement.start_or_start_range,
        )
        self.assertEqual(
            event_placement_copy.end_or_end_range, event_placement.end_or_end_range
        )

        self.assertEqual(event_placement_copy.event, event_placement.event)

        event_placement_copy.event.duration += 2

        self.assertNotEqual(event_placement_copy.event, event_placement.event)


class TimeLineTest(unittest.TestCase):
    def setUp(self):
        self.tag = "test"
        self.static_duration = core_parameters.DirectDuration(10)
        self.event = core_events.SimultaneousEvent(
            [core_events.TaggedSimpleEvent(1, tag=self.tag)]
        )
        self.timeline_dynamic = timeline_interfaces.TimeLine(duration=None)
        self.timeline_static = timeline_interfaces.TimeLine(
            duration=self.static_duration
        )
        self.timeline_tuple = (
            self.timeline_static,
            self.timeline_dynamic,
        )

    def test_register_basic(self):
        event_placement = timeline_interfaces.EventPlacement(self.event, 2, 5)
        for timeline in self.timeline_tuple:
            timeline.register(event_placement)
            event_placement_tuple = timeline.event_placement_tuple
            self.assertEqual(len(event_placement_tuple), 1)
            self.assertEqual(event_placement_tuple[0], event_placement)

    def test_register_exceeding_duration(self):
        self.assertRaises(
            timeline_utilities.ExceedDurationError,
            self.timeline_static.register,
            timeline_interfaces.EventPlacement(self.event, 8, 11),
        )

    def test_sort(self):
        event_placement0 = timeline_interfaces.EventPlacement(self.event, 2, 5)
        event_placement1 = timeline_interfaces.EventPlacement(self.event, 0, 1)
        event_placement2 = timeline_interfaces.EventPlacement(self.event, 2, 6)

        self.timeline_static.register(event_placement0)
        self.timeline_static.register(event_placement1)
        self.timeline_static.register(event_placement2)

        self.assertEqual(
            self.timeline_static.event_placement_tuple,
            (event_placement0, event_placement1, event_placement2),
        )

        self.timeline_static.sort()
        self.assertEqual(
            self.timeline_static.event_placement_tuple,
            (event_placement1, event_placement0, event_placement2),
        )

    def test_get_event_placement(self):
        event_placement0 = timeline_interfaces.EventPlacement(self.event, 0, 1)
        event_placement1 = timeline_interfaces.EventPlacement(self.event, 2, 3)
        event_placement2 = timeline_interfaces.EventPlacement(self.event, 5, 10)

        timeline = timeline_interfaces.TimeLine(
            [event_placement0, event_placement2, event_placement1]
        )

        self.assertEqual(timeline.get_event_placement(self.tag, 0), event_placement0)
        self.assertEqual(timeline.get_event_placement(self.tag, 1), event_placement1)
        self.assertEqual(timeline.get_event_placement(self.tag, 2), event_placement2)

    def test_tag_set(self):
        timeline = timeline_interfaces.TimeLine(
            [
                timeline_interfaces.EventPlacement(
                    core_events.SimultaneousEvent(
                        [
                            core_events.TaggedSimpleEvent(1, tag="abc"),
                            core_events.TaggedSimpleEvent(1, tag="def"),
                        ]
                    ),
                    0,
                    1,
                ),
                timeline_interfaces.EventPlacement(
                    core_events.SimultaneousEvent(
                        [
                            core_events.TaggedSimpleEvent(1, tag="ghi"),
                        ]
                    ),
                    10,
                    20,
                ),
            ]
        )
        self.assertEqual(timeline.tag_set, {"abc", "def", "ghi"})

    def test_unregister(self):
        event_placement = timeline_interfaces.EventPlacement(self.event, 0, 1)
        self.timeline_dynamic.register(event_placement)
        self.assertEqual(len(self.timeline_dynamic.event_placement_tuple), 1)
        self.timeline_dynamic.unregister(event_placement)
        self.assertEqual(len(self.timeline_dynamic.event_placement_tuple), 0)

    def test_unregister_error(self):
        event_placement = timeline_interfaces.EventPlacement(self.event, 0, 1)
        self.assertRaises(
            timeline_utilities.EventPlacementNotFoundError,
            self.timeline_dynamic.unregister,
            event_placement,
        )

    def test_resolve_conflicts(self):
        # First we make a simple test with only two overlapping
        # event placements. One of them should be removed when we
        # call 'resolve_conflicts'.
        event_placement_0 = timeline_interfaces.EventPlacement(self.event, 0, 1)
        event_placement_1 = timeline_interfaces.EventPlacement(self.event, 0.5, 1.5)

        self.timeline_dynamic.register(event_placement_0)
        self.timeline_dynamic.register(event_placement_1)

        self.assertEqual(len(self.timeline_dynamic.event_placement_tuple), 2)

        self.timeline_dynamic.resolve_conflicts()
        self.assertEqual(len(self.timeline_dynamic.event_placement_tuple), 1)

        self.assertTrue(
            event_placement_0 in self.timeline_dynamic.event_placement_tuple
        )

    def test_resolve_conflicts_with_different_tags(self):
        # If we add an event with a different tag, this isn't considered
        # to be a conflict.
        event_placement_0 = timeline_interfaces.EventPlacement(self.event, 0, 1)
        event_placement_1 = timeline_interfaces.EventPlacement(
            self.event.copy().set_parameter("tag", "d"), 0.5, 1.5
        )

        self.timeline_dynamic.register(event_placement_0)
        self.timeline_dynamic.register(event_placement_1)

        self.timeline_dynamic.resolve_conflicts()
        self.assertEqual(len(self.timeline_dynamic.event_placement_tuple), 2)

    def test_resolve_conflicts_with_sequential_conflicts(self):
        # Now we try to resolve sequentially appearing conflicts due to
        # a sequence of more than two overlapping event placements.
        event_placement_0 = timeline_interfaces.EventPlacement(self.event, 0, 1)
        event_placement_1 = timeline_interfaces.EventPlacement(self.event, 0.5, 1.5)
        event_placement_2 = timeline_interfaces.EventPlacement(self.event, 1, 2)

        self.timeline_dynamic.register(event_placement_0)
        self.timeline_dynamic.register(event_placement_1)
        self.timeline_dynamic.register(event_placement_2)

        self.assertEqual(len(self.timeline_dynamic.event_placement_tuple), 3)

        self.timeline_dynamic.resolve_conflicts()
        self.assertEqual(len(self.timeline_dynamic.event_placement_tuple), 2)

        self.assertTrue(
            event_placement_0 in self.timeline_dynamic.event_placement_tuple
        )
        self.assertTrue(
            event_placement_2 in self.timeline_dynamic.event_placement_tuple
        )

    def test_resolve_conflicts_with_inbetween_event_placement(self):
        # Here event_placement_0 and event_placement_1 are overlapping / have a
        # conflict. But on the global timeline, between those two event
        # placements, there is another event placement which is played by a
        # different instrument. So the expected result would be that the
        # algorithm solves the conflict between event_placement_0 and
        # event_placement_1, but leaves event_placement_2 as it is.
        #
        # For passing this test, the conflict resolution algorithm shouldn't
        # only compare two neighbour event placements (neighbour in terms of
        # following each other due to sequentially rising start time), but also
        # event placements further away from each other.
        #
        # This invariant wasn't true in the initial implementation of this
        # algorithm, which is why this test was added.
        event_placement_0 = timeline_interfaces.EventPlacement(self.event, 0, 1)
        event_placement_1 = timeline_interfaces.EventPlacement(self.event, 0.5, 1.5)
        event_placement_2 = timeline_interfaces.EventPlacement(
            self.event.copy().set_parameter("tag", "d"), 0.3, 0.5
        )

        self.timeline_dynamic.register(event_placement_0)
        self.timeline_dynamic.register(event_placement_1)
        self.timeline_dynamic.register(event_placement_2)

        self.assertEqual(len(self.timeline_dynamic.event_placement_tuple), 3)

        self.timeline_dynamic.resolve_conflicts()
        self.assertEqual(len(self.timeline_dynamic.event_placement_tuple), 2)

        self.assertTrue(
            event_placement_0 in self.timeline_dynamic.event_placement_tuple
        )
        self.assertTrue(
            event_placement_2 in self.timeline_dynamic.event_placement_tuple
        )
