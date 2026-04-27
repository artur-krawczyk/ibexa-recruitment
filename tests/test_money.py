import pytest

from discount_calculator.exceptions import CurrencyMismatchError, InvalidMoneyError
from discount_calculator.money import Money


def test_money_stores_amount_and_currency() -> None:
    m = Money(100, "EUR")
    assert m.amount == 100
    assert m.currency == "EUR"


def test_money_is_frozen() -> None:
    m = Money(100, "EUR")
    with pytest.raises(AttributeError):
        m.amount = 200  # type: ignore[misc]


@pytest.mark.parametrize(
    "amount,currency",
    [
        (-1, "EUR"),
        (1.5, "EUR"),
        (100, ""),
    ],
)
def test_money_raises_on_invalid_construction(amount: object, currency: str) -> None:
    with pytest.raises(InvalidMoneyError):
        Money(amount, currency)  # type: ignore[arg-type]


def test_money_zero_amount_is_valid() -> None:
    m = Money(0, "EUR")
    assert m.amount == 0


def test_money_equal_when_same_amount_and_currency() -> None:
    assert Money(100, "EUR") == Money(100, "EUR")


def test_money_not_equal_when_different_amount() -> None:
    assert Money(100, "EUR") != Money(200, "EUR")


def test_money_not_equal_when_different_currency() -> None:
    assert Money(100, "EUR") != Money(100, "USD")


def test_addition_same_currency_returns_sum() -> None:
    assert Money(100, "EUR") + Money(50, "EUR") == Money(150, "EUR")


def test_addition_different_currency_raises() -> None:
    with pytest.raises(CurrencyMismatchError):
        Money(100, "EUR") + Money(50, "USD")


def test_addition_returns_new_instance() -> None:
    a = Money(100, "EUR")
    b = Money(50, "EUR")
    result = a + b
    assert result is not a
    assert result is not b


def test_subtraction_same_currency_returns_difference() -> None:
    assert Money(150, "EUR") - Money(50, "EUR") == Money(100, "EUR")


def test_subtraction_different_currency_raises() -> None:
    with pytest.raises(CurrencyMismatchError):
        Money(150, "EUR") - Money(50, "USD")


def test_subtraction_result_clamped_to_zero() -> None:
    assert Money(30, "EUR") - Money(100, "EUR") == Money(0, "EUR")


def test_subtraction_exact_zero_result() -> None:
    assert Money(100, "EUR") - Money(100, "EUR") == Money(0, "EUR")


def test_multiplication_by_positive_int() -> None:
    assert Money(100, "EUR") * 3 == Money(300, "EUR")


def test_multiplication_by_zero() -> None:
    assert Money(100, "EUR") * 0 == Money(0, "EUR")


def test_multiplication_returns_new_instance() -> None:
    m = Money(100, "EUR")
    assert m * 2 is not m


@pytest.mark.parametrize("n", [-1, -10])
def test_multiplication_by_negative_raises(n: int) -> None:
    with pytest.raises(InvalidMoneyError):
        Money(100, "EUR") * n


@pytest.mark.parametrize("amount", [True, False])
def test_money_raises_on_bool_amount(amount: bool) -> None:
    with pytest.raises(InvalidMoneyError):
        Money(amount, "EUR")  # type: ignore[arg-type]


@pytest.mark.parametrize("n", [True, False])
def test_multiplication_by_bool_raises(n: bool) -> None:
    with pytest.raises(InvalidMoneyError):
        Money(100, "EUR") * n  # type: ignore[arg-type]


def test_less_than_returns_true_when_amount_is_smaller() -> None:
    assert Money(50, "EUR") < Money(100, "EUR")


def test_less_than_returns_false_when_amounts_are_equal() -> None:
    assert not (Money(100, "EUR") < Money(100, "EUR"))


def test_less_than_returns_false_when_amount_is_greater() -> None:
    assert not (Money(200, "EUR") < Money(100, "EUR"))


def test_less_than_different_currency_raises() -> None:
    with pytest.raises(CurrencyMismatchError):
        Money(50, "EUR") < Money(100, "USD")  # type: ignore[operator]  # noqa: B015
