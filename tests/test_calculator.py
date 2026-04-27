import pytest

from discount_calculator.calculator import DiscountCalculator
from discount_calculator.cart_item import CartItem
from discount_calculator.discounts import Discount, FixedDiscount, PercentageDiscount, VolumeDiscount
from discount_calculator.exceptions import CurrencyMismatchError, EmptyCartError
from discount_calculator.money import Money
from discount_calculator.percentage import Percentage
from discount_calculator.discount_policy import BestDiscountPolicy, DiscountPolicy


def make_item(
    code: str = "A",
    amount: int = 10_00,
    currency: str = "EUR",
    quantity: int = 1,
) -> CartItem:
    return CartItem(code=code, price=Money(amount, currency), quantity=quantity)


def make_calculator(
    discounts: list[Discount] | None = None,
    policy: DiscountPolicy | None = None,
) -> DiscountCalculator:
    return DiscountCalculator(
        discounts=discounts or [],
        policy=policy or BestDiscountPolicy(),
    )


def test_empty_cart_raises():
    calc = make_calculator()
    with pytest.raises(EmptyCartError):
        calc.calculate_total([])


def test_currency_mismatch_raises():
    calc = make_calculator()
    items = [make_item(currency="EUR"), make_item(currency="USD")]
    with pytest.raises(CurrencyMismatchError):
        calc.calculate_total(items)


def test_single_item_no_discounts_returns_line_total():
    calc = make_calculator()
    assert calc.calculate_total([make_item(amount=10_00, quantity=3)]) == Money(30_00, "EUR")


def test_multiple_items_no_discounts_returns_sum_of_line_totals():
    calc = make_calculator()
    items = [
        make_item(code="A", amount=5_00, quantity=2),   # 10_00
        make_item(code="B", amount=3_00, quantity=4),   # 12_00
    ]
    assert calc.calculate_total(items) == Money(22_00, "EUR")


def test_single_item_discount_reduces_total():
    discount = FixedDiscount(restricted_to=None, amount_per_unit=Money(2_00, "EUR"))
    calc = make_calculator(discounts=[discount])
    # line_total = 10_00, discount = 2_00 → 8_00
    assert calc.calculate_total([make_item(amount=10_00, quantity=1)]) == Money(8_00, "EUR")


def test_discount_not_applicable_to_item_leaves_total_unchanged():
    discount = FixedDiscount(restricted_to=frozenset({"Z"}), amount_per_unit=Money(5_00, "EUR"))
    calc = make_calculator(discounts=[discount])
    assert calc.calculate_total([make_item(code="A", amount=10_00)]) == Money(10_00, "EUR")


def test_discount_applied_per_line_independently():
    discount = FixedDiscount(restricted_to=frozenset({"A"}), amount_per_unit=Money(1_00, "EUR"))
    calc = make_calculator(discounts=[discount])
    items = [
        make_item(code="A", amount=5_00, quantity=2),   # line 10_00 − 2_00 = 8_00
        make_item(code="B", amount=4_00, quantity=1),   # line  4_00 − 0   = 4_00
    ]
    assert calc.calculate_total(items) == Money(12_00, "EUR")


def test_multiple_items_each_discounted():
    discount_a = FixedDiscount(restricted_to=frozenset({"A"}), amount_per_unit=Money(1_00, "EUR"))
    discount_b = PercentageDiscount(restricted_to=frozenset({"B"}), percentage=Percentage(50_00))
    calc = make_calculator(discounts=[discount_a, discount_b])
    items = [
        make_item(code="A", amount=10_00, quantity=1),  # 10_00 − 1_00 = 9_00
        make_item(code="B", amount=8_00,  quantity=1),  # 8_00  − 4_00 = 4_00
    ]
    assert calc.calculate_total(items) == Money(13_00, "EUR")


def test_best_discount_selected_per_line():
    small = FixedDiscount(restricted_to=None, amount_per_unit=Money(1_00, "EUR"))
    large = PercentageDiscount(restricted_to=None, percentage=Percentage(30_00))
    calc = make_calculator(discounts=[small, large])
    # line_total = 10_00; small saves 1_00, large saves 3_00 → best = large
    assert calc.calculate_total([make_item(amount=10_00)]) == Money(7_00, "EUR")


def test_discount_capped_at_line_total_does_not_go_negative():
    discount = FixedDiscount(restricted_to=None, amount_per_unit=Money(50_00, "EUR"))
    calc = make_calculator(discounts=[discount])
    # line_total = 5_00, discount raw = 50_00 → capped to 5_00 → total = 0
    assert calc.calculate_total([make_item(amount=5_00, quantity=1)]) == Money(0, "EUR")


class _FirstApplicablePolicy(DiscountPolicy):
    """Returns the saving from the first applicable discount, ignoring size."""
    def calculate(self, discounts: list[Discount], item: CartItem) -> Money:
        first = next((d for d in discounts if d.applies_to(item)), None)
        return first.calculate(item) if first is not None else Money(0, item.price.currency)


def test_custom_policy_injected_and_used():
    small = FixedDiscount(restricted_to=None, amount_per_unit=Money(1_00, "EUR"))  # first
    large = PercentageDiscount(restricted_to=None, percentage=Percentage(40_00))   # second
    calc = DiscountCalculator(discounts=[small, large], policy=_FirstApplicablePolicy())
    # _FirstApplicablePolicy picks small (saves 1_00), ignoring large (saves 4_00)
    # line_total = 10_00 − 1_00 = 9_00
    assert calc.calculate_total([make_item(amount=10_00)]) == Money(9_00, "EUR")


# ---------------------------------------------------------------------------
# Parametrized end-to-end scenarios
#
# Each tuple: (items, discounts, expected_total).
# Savings per line annotated inline so the expected total is easy to verify.
# ---------------------------------------------------------------------------

_SCENARIOS = [
    pytest.param(
        # Three items, each won by a different discount type.
        #   A: price=10_00 ×2 → line 20_00; Fixed(A,3_00)→6_00, Pct10%→2_00    → net 14_00
        #   B: price=15_00 ×1 → line 15_00; Pct40%(B)→6_00,     Pct10%→1_50   → net  9_00
        #   C: price= 8_00 ×3 → line 24_00; Volume(C,7_00,min3)→7_00, Pct10%→2_40 → net 17_00
        #   total = 40_00
        [
            CartItem(code="A", price=Money(10_00, "EUR"), quantity=2),
            CartItem(code="B", price=Money(15_00, "EUR"), quantity=1),
            CartItem(code="C", price=Money( 8_00, "EUR"), quantity=3),
        ],
        [
            FixedDiscount(frozenset({"A"}), Money(3_00, "EUR")),
            PercentageDiscount(frozenset({"B"}), Percentage(40_00)),
            VolumeDiscount(frozenset({"C"}), Money(7_00, "EUR"), min_quantity=3),
            PercentageDiscount(None, Percentage(10_00)),
        ],
        Money(40_00, "EUR"),
        id="each_line_won_by_different_discount_type",
    ),
    pytest.param(
        # High percentage beats fixed on both lines; volume inapplicable (qty < 3).
        #   A: price=50_00 ×1 → line 50_00; Fixed→5_00,  Pct25%→12_50 → net 37_50
        #   B: price=30_00 ×2 → line 60_00; Fixed→10_00, Pct25%→15_00 → net 45_00
        #   total = 82_50
        [
            CartItem(code="A", price=Money(50_00, "EUR"), quantity=1),
            CartItem(code="B", price=Money(30_00, "EUR"), quantity=2),
        ],
        [
            FixedDiscount(None, Money(5_00, "EUR")),
            PercentageDiscount(None, Percentage(25_00)),
            VolumeDiscount(None, Money(8_00, "EUR"), min_quantity=3),
        ],
        Money(82_50, "EUR"),
        id="percentage_beats_fixed_volume_inapplicable",
    ),
    pytest.param(
        # Volume wins on high-qty line; fixed wins on low-qty line (volume not triggered).
        #   X: price=10_00 ×5 → line 50_00; Volume(min3)→15_00, Fixed→10_00 → net 35_00
        #   Y: price=10_00 ×2 → line 20_00; Volume not applicable,  Fixed→4_00  → net 16_00
        #   total = 51_00
        [
            CartItem(code="X", price=Money(10_00, "EUR"), quantity=5),
            CartItem(code="Y", price=Money(10_00, "EUR"), quantity=2),
        ],
        [
            VolumeDiscount(None, Money(15_00, "EUR"), min_quantity=3),
            FixedDiscount(None, Money(2_00, "EUR")),
        ],
        Money(51_00, "EUR"),
        id="volume_wins_above_threshold_fixed_wins_below",
    ),
    pytest.param(
        # Targeted discount beats universal on matching line; universal applies elsewhere.
        #   A: price=20_00 ×1 → line 20_00; Fixed(A)→12_00, Pct50%→10_00 → net  8_00
        #   B: price=20_00 ×1 → line 20_00; Fixed(A) N/A,   Pct50%→10_00 → net 10_00
        #   total = 18_00
        [
            CartItem(code="A", price=Money(20_00, "EUR"), quantity=1),
            CartItem(code="B", price=Money(20_00, "EUR"), quantity=1),
        ],
        [
            FixedDiscount(frozenset({"A"}), Money(12_00, "EUR")),
            PercentageDiscount(None, Percentage(50_00)),
        ],
        Money(18_00, "EUR"),
        id="targeted_discount_beats_universal_on_matching_line",
    ),
    pytest.param(
        # No discount applies to any item — full price paid.
        #   A: price=10_00 ×1 → 10_00 (Fixed targets Z; Volume qty<5)
        #   B: price=10_00 ×1 → 10_00 (same)
        #   total = 20_00
        [
            CartItem(code="A", price=Money(10_00, "EUR"), quantity=1),
            CartItem(code="B", price=Money(10_00, "EUR"), quantity=1),
        ],
        [
            FixedDiscount(frozenset({"Z"}), Money(5_00, "EUR")),
            VolumeDiscount(None, Money(3_00, "EUR"), min_quantity=5),
        ],
        Money(20_00, "EUR"),
        id="no_applicable_discount_full_price_paid",
    ),
]


@pytest.mark.parametrize("items,discounts,expected", _SCENARIOS)
def test_calculate_total(items, discounts, expected):
    calc = DiscountCalculator(discounts=discounts, policy=BestDiscountPolicy())
    assert calc.calculate_total(items) == expected
