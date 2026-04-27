from __future__ import annotations

from dataclasses import dataclass

from discount_calculator.exceptions import InvalidCartItemError
from discount_calculator.money import Money


@dataclass(frozen=True)
class CartItem:
    code: str
    price: Money
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvalidCartItemError(f"quantity must be positive, got {self.quantity}")

    def line_total(self) -> Money:
        return self.price * self.quantity
