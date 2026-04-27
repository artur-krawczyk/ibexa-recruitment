from collections.abc import Callable

import pytest

from discount_calculator.cart_item import CartItem
from discount_calculator.money import Money


@pytest.fixture
def make_item() -> Callable[..., CartItem]:
    def _make(
        code: str = "A",
        amount: int = 10_00,
        currency: str = "EUR",
        quantity: int = 1,
    ) -> CartItem:
        return CartItem(code=code, price=Money(amount, currency), quantity=quantity)

    return _make
