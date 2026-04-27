from collections.abc import Callable

import pytest

from discount_calculator.cart_item import CartItem
from discount_calculator.discount_policy import BestDiscountPolicy
from discount_calculator.discounts import Discount, FixedDiscount, PercentageDiscount, VolumeDiscount
from discount_calculator.money import Money
from discount_calculator.percentage import Percentage


def test_returns_zero_when_no_discounts(make_item: Callable[..., CartItem]) -> None:
    policy = BestDiscountPolicy()
    assert policy.calculate([], make_item()) == Money(0, "EUR")


def test_returns_zero_when_no_discount_applies(make_item: Callable[..., CartItem]) -> None:
    policy = BestDiscountPolicy()
    item = make_item(code="A")
    discount = FixedDiscount(restricted_to=frozenset({"B"}), amount_per_unit=Money(1_00, "EUR"))
    assert policy.calculate([discount], item) == Money(0, "EUR")


def test_returns_saving_of_single_applicable_discount(make_item: Callable[..., CartItem]) -> None:
    policy = BestDiscountPolicy()
    item = make_item(amount=10_00, quantity=1)
    discount = FixedDiscount(restricted_to=None, amount_per_unit=Money(2_00, "EUR"))
    assert policy.calculate([discount], item) == Money(2_00, "EUR")


def test_picks_larger_reduction_over_smaller(make_item: Callable[..., CartItem]) -> None:
    policy = BestDiscountPolicy()
    item = make_item(amount=10_00, quantity=1)  # line_total = 10_00
    small = FixedDiscount(restricted_to=None, amount_per_unit=Money(1_00, "EUR"))  # saves 1_00
    large = PercentageDiscount(restricted_to=None, percentage=Percentage(30_00))  # saves 3_00
    assert policy.calculate([small, large], item) == Money(3_00, "EUR")


def test_picks_larger_reduction_regardless_of_order(make_item: Callable[..., CartItem]) -> None:
    policy = BestDiscountPolicy()
    item = make_item(amount=10_00, quantity=1)
    large = PercentageDiscount(restricted_to=None, percentage=Percentage(30_00))  # saves 3_00
    small = FixedDiscount(restricted_to=None, amount_per_unit=Money(1_00, "EUR"))  # saves 1_00
    assert policy.calculate([large, small], item) == Money(3_00, "EUR")


def test_tie_broken_by_insertion_order(make_item: Callable[..., CartItem]) -> None:
    policy = BestDiscountPolicy()
    item = make_item(amount=10_00, quantity=1)  # line_total = 10_00
    first = FixedDiscount(restricted_to=None, amount_per_unit=Money(5_00, "EUR"))
    second = PercentageDiscount(restricted_to=None, percentage=Percentage(50_00))  # also 5_00
    # both save 5_00; first in insertion order is returned
    assert policy.calculate([first, second], item) == Money(5_00, "EUR")


def test_skips_non_applicable_returns_saving_of_applicable(make_item: Callable[..., CartItem]) -> None:
    policy = BestDiscountPolicy()
    item = make_item(code="A", amount=10_00, quantity=1)
    non_applicable = FixedDiscount(restricted_to=frozenset({"B"}), amount_per_unit=Money(9_00, "EUR"))
    applicable = FixedDiscount(restricted_to=frozenset({"A"}), amount_per_unit=Money(2_00, "EUR"))
    assert policy.calculate([non_applicable, applicable], item) == Money(2_00, "EUR")


def test_returns_zero_below_volume_min_quantity(make_item: Callable[..., CartItem]) -> None:
    policy = BestDiscountPolicy()
    item = make_item(amount=10_00, quantity=2)
    volume = VolumeDiscount(restricted_to=None, amount=Money(5_00, "EUR"), min_quantity=3)
    assert policy.calculate([volume], item) == Money(0, "EUR")


def test_returns_saving_at_volume_min_quantity(make_item: Callable[..., CartItem]) -> None:
    policy = BestDiscountPolicy()
    item = make_item(amount=10_00, quantity=3)
    volume = VolumeDiscount(restricted_to=None, amount=Money(5_00, "EUR"), min_quantity=3)
    assert policy.calculate([volume], item) == Money(5_00, "EUR")


_SCENARIOS = [
    pytest.param(
        # qty=3, price=10_00 EUR  →  line_total=30_00
        CartItem(code="A", price=Money(10_00, "EUR"), quantity=3),
        [
            FixedDiscount(None, Money(2_00, "EUR")),  # saves  6_00
            PercentageDiscount(None, Percentage(15_00)),  # saves  4_50
            VolumeDiscount(None, Money(8_00, "EUR"), min_quantity=3),  # saves  8_00  ← best
        ],
        Money(8_00, "EUR"),
        id="volume_beats_fixed_and_percentage",
    ),
    pytest.param(
        # qty=2, price=5_00 EUR  →  line_total=10_00
        CartItem(code="B", price=Money(5_00, "EUR"), quantity=2),
        [
            FixedDiscount(frozenset({"B"}), Money(3_00, "EUR")),  # saves  6_00  ← best
            PercentageDiscount(frozenset({"B"}), Percentage(50_00)),  # saves  5_00
            VolumeDiscount(frozenset({"B"}), Money(7_00, "EUR"), min_quantity=5),  # NOT applicable
        ],
        Money(6_00, "EUR"),
        id="fixed_beats_percentage_volume_inapplicable",
    ),
    pytest.param(
        # qty=4, price=20_00 EUR  →  line_total=80_00
        CartItem(code="C", price=Money(20_00, "EUR"), quantity=4),
        [
            FixedDiscount(None, Money(5_00, "EUR")),  # saves 20_00
            PercentageDiscount(None, Percentage(30_00)),  # saves 24_00  ← best
            VolumeDiscount(None, Money(15_00, "EUR"), min_quantity=3),  # saves 15_00
        ],
        Money(24_00, "EUR"),
        id="percentage_beats_fixed_and_volume",
    ),
    pytest.param(
        # qty=1, price=100_00 EUR  →  line_total=100_00; two discounts inapplicable
        CartItem(code="D", price=Money(100_00, "EUR"), quantity=1),
        [
            FixedDiscount(frozenset({"D"}), Money(40_00, "EUR")),  # saves 40_00  ← best
            PercentageDiscount(frozenset({"A"}), Percentage(50_00)),  # NOT applicable
            VolumeDiscount(frozenset({"D"}), Money(60_00, "EUR"), min_quantity=2),  # NOT applicable
        ],
        Money(40_00, "EUR"),
        id="only_one_applicable_wins",
    ),
    pytest.param(
        # qty=5, price=3_00 EUR  →  line_total=15_00; fixed targets wrong code
        CartItem(code="A", price=Money(3_00, "EUR"), quantity=5),
        [
            FixedDiscount(frozenset({"B"}), Money(10_00, "EUR")),  # NOT applicable
            PercentageDiscount(None, Percentage(20_00)),  # saves  3_00
            VolumeDiscount(frozenset({"A"}), Money(5_00, "EUR"), min_quantity=4),  # saves  5_00  ← best
        ],
        Money(5_00, "EUR"),
        id="volume_beats_percentage_fixed_inapplicable",
    ),
    pytest.param(
        # qty=1, price=10_00 EUR  →  line_total=10_00; three-way tie
        CartItem(code="X", price=Money(10_00, "EUR"), quantity=1),
        [
            FixedDiscount(None, Money(5_00, "EUR")),  # saves 5_00  ← first in
            PercentageDiscount(None, Percentage(50_00)),  # saves 5_00  tied
            VolumeDiscount(None, Money(5_00, "EUR"), min_quantity=1),  # saves 5_00  tied
        ],
        Money(5_00, "EUR"),
        id="three_way_tie_insertion_order_wins",
    ),
]


@pytest.mark.parametrize("item,discounts,expected_saving", _SCENARIOS)
def test_calculate_returns_best_saving(item: CartItem, discounts: list[Discount], expected_saving: Money) -> None:
    policy = BestDiscountPolicy()
    assert policy.calculate(discounts, item) == expected_saving
