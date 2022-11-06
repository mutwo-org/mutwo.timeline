class EventPlacementRegisterError(Exception):
    def __init__(self, event_placement_to_register, message: str = ""):
        super().__init__(
            "Problem with EventPlacement on tag = "
            f"'{event_placement_to_register.event.tag}': {message}"
        )


class OverlappingEventPlacementError(EventPlacementRegisterError):
    def __init__(self, event_placement_to_register, event_placement_which_overlaps):
        super().__init__(
            event_placement_to_register,
            f"Can't register EventPlacement '{event_placement_to_register}'"
            " because it overlaps with already "
            f"registerd EventPlacement '{event_placement_which_overlaps}'.",
        )


class ExceedDurationError(EventPlacementRegisterError):
    def __init__(self, event_placement_to_register, duration):
        super().__init__(
            event_placement_to_register,
            f"EventPlacement '{event_placement_to_register} "
            "exceed predefined static duration = '{duration}' of "
            "TimeLine.",
        )
