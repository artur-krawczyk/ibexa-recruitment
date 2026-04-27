from abc import ABC, abstractmethod
from dataclasses import dataclass

from discount_calculator.cart_item import CartItem
from discount_calculator.exceptions import InvalidDiscountError
from discount_calculator.money import Money
from discount_calculator.percentage import Percentage


class Discount(ABC):
    restricted_to: frozenset[str] | None

    def applies_to(self, item: CartItem) -> bool:
        return self.restricted_to is None or item.code in self.restricted_to

    @abstractmethod
    def calculate(self, item: CartItem) -> Money: ...


@dataclass(frozen=True)
class FixedDiscount(Discount):
    restricted_to: frozenset[str] | None
    amount_per_unit: Money

    def calculate(self, item: CartItem) -> Money:
        uncapped = self.amount_per_unit * item.quantity
        return min(uncapped, item.line_total())


@dataclass(frozen=True)
class PercentageDiscount(Discount):
    restricted_to: frozenset[str] | None
    percentage: Percentage

    def calculate(self, item: CartItem) -> Money:
        return self.percentage.apply_to(item.line_total())


@dataclass(frozen=True)
class VolumeDiscount(Discount):
    restricted_to: frozenset[str] | None
    amount: Money
    min_quantity: int

    def __post_init__(self) -> None:
        if isinstance(self.min_quantity, bool) or not isinstance(self.min_quantity, int):
            raise InvalidDiscountError(f"min_quantity must be an int, got {type(self.min_quantity).__name__}")
        if self.min_quantity <= 0:
            raise InvalidDiscountError(f"min_quantity must be positive, got {self.min_quantity}")

    def applies_to(self, item: CartItem) -> bool:
        return super().applies_to(item) and item.quantity >= self.min_quantity

    def calculate(self, item: CartItem) -> Money:
        return min(self.amount, item.line_total())
