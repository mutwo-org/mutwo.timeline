import typing

__all__ = (
    "EventPlacementRegisterError",
    "ExceedDurationError",
    "EventPlacementNotFoundError",
    "TooSmallRangeWarning",
)


class EventPlacementRegisterError(Exception):
    def __init__(self, event_placement_to_register, message: str = ""):
        super().__init__(
            "Problem with EventPlacement on tag_tuple = "
            f"'{event_placement_to_register.tag_tuple}': {message}"
        )


class ExceedDurationError(EventPlacementRegisterError):
    def __init__(self, event_placement_to_register, duration):
        super().__init__(
            event_placement_to_register,
            f"EventPlacement '{event_placement_to_register} "
            "exceed predefined static duration = '{duration}' of "
            "TimeLine.",
        )


class EventPlacementNotFoundError(Exception):
    def __init__(
        self,
        tag: typing.Optional[str] = None,
        index: typing.Optional[int] = None,
        event_placement=None,
    ):
        if event_placement:
            m = f"Can't find EventPlacement '{event_placement}' inside TimeLine!"
        elif tag is not None:
            m = (
                f"Can't find EventPlacement with tag = '{tag}' "
                f"and index = '{index}' in TimeLine!"
            )
        else:
            raise TypeError("Need to provide either event_placement or tag/index!")
        super().__init__(m)


class TooSmallRangeWarning(Warning):
    def __init__(self, event_placement, time_range):
        super().__init__(
            f"Found too small difference in time range '{time_range}' of "
            f"'{event_placement}'. Auto set to only one value. Increase "
            "'mutwo.core_parameters.configurations.ROUND_DURATION_TO_N_DIGITS'"
            " if you need higher precision."
        )
