from dataclasses import dataclass

from discount_calculator.exceptions import InvalidCartItemError
from discount_calculator.money import Money


@dataclass(frozen=True)
class CartItem:
    code: str
    price: Money
    quantity: int

    def __post_init__(self) -> None:
        if not self.code:
            raise InvalidCartItemError("code must be a non-empty string")
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise InvalidCartItemError(f"quantity must be an int, got {type(self.quantity).__name__}")
        if self.quantity <= 0:
            raise InvalidCartItemError(f"quantity must be positive, got {self.quantity}")

    def line_total(self) -> Money:
        return self.price * self.quantity
