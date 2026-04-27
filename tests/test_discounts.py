from collections.abc import Callable

import pytest

from discount_calculator.cart_item import CartItem
from discount_calculator.discounts import Discount, FixedDiscount, PercentageDiscount, VolumeDiscount
from discount_calculator.exceptions import CurrencyMismatchError, InvalidDiscountError
from discount_calculator.money import Money
from discount_calculator.percentage import Percentage


def test_discount_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Discount(restricted_to=None)  # type: ignore[abstract]


@pytest.mark.parametrize(
    "restricted_to,item_code,expected",
    [
        (None, "XYZ", True),
        (frozenset({"A"}), "A", True),
        (frozenset({"A"}), "B", False),
    ],
)
def test_fixed_discount_applies_to(
    restricted_to: frozenset[str] | None,
    item_code: str,
    expected: bool,
    make_item: Callable[..., CartItem],
) -> None:
    discount = FixedDiscount(restricted_to=restricted_to, amount_per_unit=Money(1_00, "EUR"))
    assert discount.applies_to(make_item(item_code)) is expected


def test_fixed_discount_calculate_returns_amount_per_unit_times_quantity(
    make_item: Callable[..., CartItem],
) -> None:
    item = make_item(amount=10_00, quantity=3)
    discount = FixedDiscount(restricted_to=None, amount_per_unit=Money(2_00, "EUR"))
    assert discount.calculate(item) == Money(6_00, "EUR")


def test_fixed_discount_calculate_capped_at_line_total(
    make_item: Callable[..., CartItem],
) -> None:
    item = make_item(amount=1_00, quantity=2)  # line_total = 2_00
    discount = FixedDiscount(restricted_to=None, amount_per_unit=Money(2_00, "EUR"))  # raw = 4_00
    assert discount.calculate(item) == Money(2_00, "EUR")


def test_fixed_discount_calculate_raises_on_currency_mismatch(
    make_item: Callable[..., CartItem],
) -> None:
    item = make_item(currency="EUR")
    discount = FixedDiscount(restricted_to=None, amount_per_unit=Money(1_00, "USD"))
    with pytest.raises(CurrencyMismatchError):
        discount.calculate(item)


@pytest.mark.parametrize(
    "restricted_to,item_code,expected",
    [
        (None, "XYZ", True),
        (frozenset({"B"}), "B", True),
        (frozenset({"B"}), "A", False),
    ],
)
def test_percentage_discount_applies_to(
    restricted_to: frozenset[str] | None,
    item_code: str,
    expected: bool,
    make_item: Callable[..., CartItem],
) -> None:
    discount = PercentageDiscount(restricted_to=restricted_to, percentage=Percentage(10_00))
    assert discount.applies_to(make_item(item_code)) is expected


def test_percentage_discount_calculate_returns_percentage_of_line_total(
    make_item: Callable[..., CartItem],
) -> None:
    item = make_item(amount=10_00, quantity=2)  # line_total = 20_00
    discount = PercentageDiscount(restricted_to=None, percentage=Percentage(10_00))  # 10%
    assert discount.calculate(item) == Money(2_00, "EUR")


def test_percentage_discount_calculate_rounds_half_up(
    make_item: Callable[..., CartItem],
) -> None:
    # line_total = 3 cents, 50% → 1.5 → ROUND_HALF_UP → 2
    item = make_item(amount=3, quantity=1)
    discount = PercentageDiscount(restricted_to=None, percentage=Percentage(50_00))
    assert discount.calculate(item) == Money(2, "EUR")


def test_percentage_discount_calculate_full_discount_equals_line_total(
    make_item: Callable[..., CartItem],
) -> None:
    item = make_item(amount=1_00, quantity=1)
    discount = PercentageDiscount(restricted_to=None, percentage=Percentage(100_00))  # 100%
    assert discount.calculate(item) == Money(1_00, "EUR")


@pytest.mark.parametrize(
    "restricted_to,item_code,quantity,expected",
    [
        (None, "A", 3, True),
        (None, "A", 5, True),
        (None, "A", 2, False),
        (frozenset({"X"}), "Y", 5, False),
        (frozenset({"X"}), "X", 3, True),
    ],
)
def test_volume_discount_applies_to(
    restricted_to: frozenset[str] | None,
    item_code: str,
    quantity: int,
    expected: bool,
    make_item: Callable[..., CartItem],
) -> None:
    discount = VolumeDiscount(restricted_to=restricted_to, amount=Money(5_00, "EUR"), min_quantity=3)
    assert discount.applies_to(make_item(code=item_code, quantity=quantity)) is expected


def test_volume_discount_calculate_returns_flat_amount(
    make_item: Callable[..., CartItem],
) -> None:
    item = make_item(amount=10_00, quantity=3)  # line_total = 30_00
    discount = VolumeDiscount(restricted_to=None, amount=Money(5_00, "EUR"), min_quantity=3)
    assert discount.calculate(item) == Money(5_00, "EUR")


def test_volume_discount_calculate_capped_at_line_total(
    make_item: Callable[..., CartItem],
) -> None:
    item = make_item(amount=1_00, quantity=2)  # line_total = 2_00
    discount = VolumeDiscount(restricted_to=None, amount=Money(50_00, "EUR"), min_quantity=2)
    assert discount.calculate(item) == Money(2_00, "EUR")


def test_volume_discount_calculate_raises_on_currency_mismatch(
    make_item: Callable[..., CartItem],
) -> None:
    item = make_item(currency="EUR", quantity=3)
    discount = VolumeDiscount(restricted_to=None, amount=Money(5_00, "USD"), min_quantity=3)
    with pytest.raises(CurrencyMismatchError):
        discount.calculate(item)


@pytest.mark.parametrize("min_quantity", [0, -1, -10])
def test_volume_discount_raises_on_non_positive_min_quantity(min_quantity: int) -> None:
    with pytest.raises(InvalidDiscountError):
        VolumeDiscount(restricted_to=None, amount=Money(5_00, "EUR"), min_quantity=min_quantity)


@pytest.mark.parametrize("min_quantity", [True, False])
def test_volume_discount_raises_on_bool_min_quantity(min_quantity: bool) -> None:
    with pytest.raises(InvalidDiscountError):
        VolumeDiscount(restricted_to=None, amount=Money(5_00, "EUR"), min_quantity=min_quantity)  # type: ignore[arg-type]
