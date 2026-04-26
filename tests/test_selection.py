import pytest

from discount_calculator.cart_item import CartItem
from discount_calculator.discounts import FixedDiscount, PercentageDiscount, VolumeDiscount
from discount_calculator.money import Money
from discount_calculator.percentage import Percentage
from discount_calculator.selection import BestDiscountSelector, DiscountSelector


def make_item(
    code: str = "A",
    amount: int = 10_00,
    currency: str = "EUR",
    quantity: int = 1,
) -> CartItem:
    return CartItem(code=code, price=Money(amount, currency), quantity=quantity)


def test_best_discount_selector_implements_protocol():
    assert isinstance(BestDiscountSelector(), DiscountSelector)


def test_returns_none_when_no_discounts():
    selector = BestDiscountSelector()
    item = make_item()
    assert selector.select([], item) is None


def test_returns_none_when_no_discount_applies():
    selector = BestDiscountSelector()
    item = make_item(code="A")
    discount = FixedDiscount(product_codes=frozenset({"B"}), amount_per_unit=Money(1_00, "EUR"))
    assert selector.select([discount], item) is None


def test_returns_single_applicable_discount():
    selector = BestDiscountSelector()
    item = make_item(amount=10_00, quantity=1)
    discount = FixedDiscount(product_codes=None, amount_per_unit=Money(2_00, "EUR"))
    assert selector.select([discount], item) is discount


def test_picks_larger_reduction_over_smaller():
    selector = BestDiscountSelector()
    item = make_item(amount=10_00, quantity=1)  # line_total = 10_00
    small = FixedDiscount(product_codes=None, amount_per_unit=Money(1_00, "EUR"))   # saves 1_00
    large = PercentageDiscount(product_codes=None, percentage=Percentage(30_00))    # saves 3_00
    assert selector.select([small, large], item) is large


def test_picks_larger_reduction_regardless_of_order():
    selector = BestDiscountSelector()
    item = make_item(amount=10_00, quantity=1)
    large = PercentageDiscount(product_codes=None, percentage=Percentage(30_00))    # saves 3_00
    small = FixedDiscount(product_codes=None, amount_per_unit=Money(1_00, "EUR"))   # saves 1_00
    assert selector.select([large, small], item) is large


def test_tie_broken_by_insertion_order():
    selector = BestDiscountSelector()
    item = make_item(amount=10_00, quantity=1)  # line_total = 10_00
    first = FixedDiscount(product_codes=None, amount_per_unit=Money(5_00, "EUR"))
    second = PercentageDiscount(product_codes=None, percentage=Percentage(50_00))   # also 5_00
    assert selector.select([first, second], item) is first


def test_skips_non_applicable_and_picks_applicable():
    selector = BestDiscountSelector()
    item = make_item(code="A", amount=10_00, quantity=1)
    non_applicable = FixedDiscount(product_codes=frozenset({"B"}), amount_per_unit=Money(9_00, "EUR"))
    applicable = FixedDiscount(product_codes=frozenset({"A"}), amount_per_unit=Money(2_00, "EUR"))
    assert selector.select([non_applicable, applicable], item) is applicable


def test_volume_discount_not_returned_below_min_quantity():
    selector = BestDiscountSelector()
    item = make_item(amount=10_00, quantity=2)
    volume = VolumeDiscount(product_codes=None, amount=Money(5_00, "EUR"), min_quantity=3)
    assert selector.select([volume], item) is None


def test_volume_discount_returned_at_min_quantity():
    selector = BestDiscountSelector()
    item = make_item(amount=10_00, quantity=3)
    volume = VolumeDiscount(product_codes=None, amount=Money(5_00, "EUR"), min_quantity=3)
    assert selector.select([volume], item) is volume


# ---------------------------------------------------------------------------
# Parametrized multi-discount scenarios
#
# Each tuple is (item, discounts_list, expected_winner_index).
# Savings are annotated so the expected winner is easy to verify by reading.
# ---------------------------------------------------------------------------

_SCENARIOS = [
    pytest.param(
        # qty=3, price=10_00 EUR  →  line_total=30_00
        CartItem(code="A", price=Money(10_00, "EUR"), quantity=3),
        [
            FixedDiscount(None, Money(2_00, "EUR")),          # saves 6_00  (idx 0)
            PercentageDiscount(None, Percentage(15_00)),       # saves 4_50  (idx 1)
            VolumeDiscount(None, Money(8_00, "EUR"), min_quantity=3),  # saves 8_00  (idx 2)
        ],
        2,
        id="volume_beats_fixed_and_percentage",
    ),
    pytest.param(
        # qty=2, price=5_00 EUR  →  line_total=10_00
        CartItem(code="B", price=Money(5_00, "EUR"), quantity=2),
        [
            FixedDiscount(frozenset({"B"}), Money(3_00, "EUR")),       # saves 6_00  (idx 0)
            PercentageDiscount(frozenset({"B"}), Percentage(50_00)),   # saves 5_00  (idx 1)
            VolumeDiscount(frozenset({"B"}), Money(7_00, "EUR"), min_quantity=5),  # NOT applicable (qty<5)
        ],
        0,
        id="fixed_beats_percentage_volume_inapplicable",
    ),
    pytest.param(
        # qty=4, price=20_00 EUR  →  line_total=80_00
        CartItem(code="C", price=Money(20_00, "EUR"), quantity=4),
        [
            FixedDiscount(None, Money(5_00, "EUR")),           # saves 20_00 (idx 0)
            PercentageDiscount(None, Percentage(30_00)),        # saves 24_00 (idx 1)
            VolumeDiscount(None, Money(15_00, "EUR"), min_quantity=3), # saves 15_00 (idx 2)
        ],
        1,
        id="percentage_beats_fixed_and_volume",
    ),
    pytest.param(
        # qty=1, price=100_00 EUR  →  line_total=100_00; two discounts are inapplicable
        CartItem(code="D", price=Money(100_00, "EUR"), quantity=1),
        [
            FixedDiscount(frozenset({"D"}), Money(40_00, "EUR")),      # saves 40_00 (idx 0)
            PercentageDiscount(frozenset({"A"}), Percentage(50_00)),   # NOT applicable (wrong code)
            VolumeDiscount(frozenset({"D"}), Money(60_00, "EUR"), min_quantity=2),  # NOT applicable (qty<2)
        ],
        0,
        id="only_one_applicable_wins",
    ),
    pytest.param(
        # qty=5, price=3_00 EUR  →  line_total=15_00; fixed targets wrong code
        CartItem(code="A", price=Money(3_00, "EUR"), quantity=5),
        [
            FixedDiscount(frozenset({"B"}), Money(10_00, "EUR")),      # NOT applicable (wrong code)
            PercentageDiscount(None, Percentage(20_00)),                # saves  3_00  (idx 1)
            VolumeDiscount(frozenset({"A"}), Money(5_00, "EUR"), min_quantity=4),   # saves  5_00  (idx 2)
        ],
        2,
        id="volume_beats_percentage_fixed_inapplicable",
    ),
    pytest.param(
        # qty=1, price=10_00 EUR  →  line_total=10_00; three-way tie on savings amount
        # tie-break: insertion order → index 0 wins
        CartItem(code="X", price=Money(10_00, "EUR"), quantity=1),
        [
            FixedDiscount(None, Money(5_00, "EUR")),           # saves 5_00 (idx 0)  ← first in
            PercentageDiscount(None, Percentage(50_00)),        # saves 5_00 (idx 1)  tied
            VolumeDiscount(None, Money(5_00, "EUR"), min_quantity=1),  # saves 5_00 (idx 2)  tied
        ],
        0,
        id="three_way_tie_insertion_order_wins",
    ),
]


@pytest.mark.parametrize("item,discounts,expected_index", _SCENARIOS)
def test_best_discount_wins(item, discounts, expected_index):
    selector = BestDiscountSelector()
    assert selector.select(discounts, item) is discounts[expected_index]
