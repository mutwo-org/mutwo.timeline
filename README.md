# mutwo.timeline

[![Build Status](https://circleci.com/gh/mutwo-org/mutwo.timeline.svg?style=shield)](https://circleci.com/gh/mutwo-org/mutwo.timeline)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version](https://badge.fury.io/py/mutwo.timeline.svg)](https://badge.fury.io/py/mutwo.timeline)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Timeline extension for event based library [Mutwo](https://github.com/mutwo-org/mutwo.core).

`Mutwo` events usually follow an approach of relative placement in time.
This means each event has a duration, and if there is a sequence of events
the second event will start after the first event finishes. So the start
and end time of any event dependent on all events which happens before the
given event. This extension implements the possibility to model events with
independent start and end times in `mutwo`.

This extension implements:

- `mutwo.timeline_converters`
- `mutwo.timeline_interfaces`
- `mutwo.timeline_utilities`

### Installation

mutwo.timeline is available on [pypi](https://pypi.org/project/mutwo.timeline/) and can be installed via pip:

```sh
pip3 install mutwo.timeline
```
