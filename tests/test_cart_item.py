import pytest

from discount_calculator.cart_item import CartItem
from discount_calculator.exceptions import InvalidCartItemError
from discount_calculator.money import Money


def test_cart_item_stores_code_price_quantity() -> None:
    item = CartItem("SKU-1", Money(100, "EUR"), 3)
    assert item.code == "SKU-1"
    assert item.price == Money(100, "EUR")
    assert item.quantity == 3


def test_cart_item_is_frozen() -> None:
    item = CartItem("SKU-1", Money(100, "EUR"), 1)
    with pytest.raises(AttributeError):
        item.quantity = 5  # type: ignore[misc]


@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_cart_item_raises_on_non_positive_quantity(quantity: int) -> None:
    with pytest.raises(InvalidCartItemError):
        CartItem("SKU-1", Money(100, "EUR"), quantity)


def test_line_total_is_price_times_quantity() -> None:
    item = CartItem("SKU-1", Money(150, "EUR"), 4)
    assert item.line_total() == Money(600, "EUR")


def test_cart_item_raises_on_empty_code() -> None:
    with pytest.raises(InvalidCartItemError):
        CartItem("", Money(100, "EUR"), 1)


@pytest.mark.parametrize("quantity", [True, False])
def test_cart_item_raises_on_bool_quantity(quantity: bool) -> None:
    with pytest.raises(InvalidCartItemError):
        CartItem("SKU-1", Money(100, "EUR"), quantity)  # type: ignore[arg-type]
