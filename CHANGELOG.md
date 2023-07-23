# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added
- `is_conflict` keyword argument to `timeline_interfaces.TimeLine.resolve_conflicts`

### Changed
- Order of 'TaggedSimultaneousEvent' in 'SimultaneousEvent' returned by 'TimeLineToSimultaneousEvent' is always the same now.


## [0.4.0] - 2023-05-13

### Added
- `timeline_interfaces.TimeLine.resolve_conflicts` [to fix overlapping conflicts](https://github.com/mutwo-org/mutwo.timeline/commit/4e0153851cd7a51daa9b3530acfed53b18c422be)
- `timeline_interfaces.TimeLine.unregister` [to unregister `EventPlacement` from a time line](https://github.com/mutwo-org/mutwo.timeline/commit/17f42450a45baca0115f5f3b2b06ad5e765d31c4)


## [0.3.0] - 2022-11-08

### Added
- `timeline_converters.EventPlacementTupleToGaplessEventPlacementTuple`
- `timeline_converters.EventPlacementTupleToSplitEventPlacementDict`
- `timeline_converters.TimeLineToEventPlacementTuple`


## [0.2.0] - 2022-11-07

### Changed
- `timeline_events` to `timeline_interfaces` [see here](ab2cb2bbc086014eb9b60db26679409a36142d68)
    - `timeline_events.TimeLine` to `timeline_interfaces.TimeLine`
    - `timeline_events.EventPlacement` to `timeline_interfaces.EventPlacement`
- `EventPlacement` to support multiple tagged events in the same `EventPlacement`

### Removed
- overlap checks in `TimeLine.register`
- `timeline_converters.EventPlacementTupleToSequentialEvent`: replaced by more powerful `timeline_converters.TimeLineToSimultaneousEvent`


## [0.1.0] - 2022-11-06

Initial release of `mutwo.timeline`.
