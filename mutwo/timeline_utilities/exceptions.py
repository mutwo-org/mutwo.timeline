__all__ = (
    "EventPlacementRegisterError",
    "ExceedDurationError",
    "EventPlacementNotFoundError",
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
    def __init__(self, tag: str, index: int):
        super().__init__(
            f"Can't find EventPlacement with tag = '{tag}' "
            f"and index = '{index}' in TimeLine!"
        )
