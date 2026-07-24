import pytest

from src.domain.preventive_plans.validation import InvalidPlanStatusTransitionError, validate_status_transition
from src.domain.shared.enums import PlanStatus


@pytest.mark.parametrize(
    "current,new",
    [
        (PlanStatus.PROPOSED, PlanStatus.APPROVED),
        (PlanStatus.PROPOSED, PlanStatus.REJECTED),
        (PlanStatus.APPROVED, PlanStatus.IN_PROGRESS),
        (PlanStatus.APPROVED, PlanStatus.CANCELLED),
        (PlanStatus.IN_PROGRESS, PlanStatus.COMPLETED),
        (PlanStatus.IN_PROGRESS, PlanStatus.CANCELLED),
    ],
)
def test_valid_transitions_do_not_raise(current: PlanStatus, new: PlanStatus) -> None:
    validate_status_transition(current, new)


@pytest.mark.parametrize(
    "current,new",
    [
        (PlanStatus.PROPOSED, PlanStatus.COMPLETED),
        (PlanStatus.PROPOSED, PlanStatus.IN_PROGRESS),
        (PlanStatus.REJECTED, PlanStatus.APPROVED),
        (PlanStatus.COMPLETED, PlanStatus.IN_PROGRESS),
        (PlanStatus.CANCELLED, PlanStatus.PROPOSED),
        (PlanStatus.APPROVED, PlanStatus.PROPOSED),
    ],
)
def test_invalid_transitions_raise(current: PlanStatus, new: PlanStatus) -> None:
    with pytest.raises(InvalidPlanStatusTransitionError):
        validate_status_transition(current, new)
