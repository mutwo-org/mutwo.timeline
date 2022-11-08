# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

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
