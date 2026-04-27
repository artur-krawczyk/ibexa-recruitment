import pytest

from discount_calculator.exceptions import InvalidPercentageError
from discount_calculator.money import Money
from discount_calculator.percentage import Percentage


def test_percentage_stores_basis_points() -> None:
    p = Percentage(1000)
    assert p.basis_points == 1000


def test_percentage_is_frozen() -> None:
    p = Percentage(1000)
    with pytest.raises(AttributeError):
        p.basis_points = 500  # type: ignore[misc]


@pytest.mark.parametrize("bps", [-1, 10001])
def test_percentage_raises_on_invalid_basis_points(bps: int) -> None:
    with pytest.raises(InvalidPercentageError):
        Percentage(bps)


@pytest.mark.parametrize("bps", [10.0, 0.5, True, False])
def test_percentage_raises_on_non_int_basis_points(bps: object) -> None:
    with pytest.raises(InvalidPercentageError):
        Percentage(bps)  # type: ignore[arg-type]


@pytest.mark.parametrize("bps", [0, 1, 5000, 9999, 10000])
def test_percentage_boundary_values_are_valid(bps: int) -> None:
    assert Percentage(bps).basis_points == bps


def test_percentage_equal_when_same_basis_points() -> None:
    assert Percentage(1000) == Percentage(1000)


def test_percentage_not_equal_when_different_basis_points() -> None:
    assert Percentage(1000) != Percentage(2000)


def test_apply_to_returns_correct_amount() -> None:
    result = Percentage(1000).apply_to(Money(200_00, "EUR"))
    assert result == Money(20_00, "EUR")


def test_apply_to_preserves_currency() -> None:
    result = Percentage(5000).apply_to(Money(100_00, "USD"))
    assert result.currency == "USD"


def test_apply_to_rounds_down_when_fraction_below_half() -> None:
    result = Percentage(3333).apply_to(Money(1, "EUR"))
    assert result == Money(0, "EUR")


def test_apply_to_rounds_up_at_exactly_half() -> None:
    result = Percentage(5000).apply_to(Money(1, "EUR"))
    assert result == Money(1, "EUR")


def test_apply_to_zero_percentage_returns_zero() -> None:
    result = Percentage(0).apply_to(Money(500_00, "EUR"))
    assert result == Money(0, "EUR")


def test_apply_to_full_percentage_returns_full_amount() -> None:
    result = Percentage(10000).apply_to(Money(500_00, "EUR"))
    assert result == Money(500_00, "EUR")
