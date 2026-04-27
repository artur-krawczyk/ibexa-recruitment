from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from discount_calculator.cart_item import CartItem
from discount_calculator.exceptions import CurrencyMismatchError
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
        if item.price.currency != self.amount_per_unit.currency:
            raise CurrencyMismatchError(
                f"cannot mix {item.price.currency} and {self.amount_per_unit.currency}"
            )
        raw = self.amount_per_unit * item.quantity
        line_total = item.line_total()
        return Money(min(raw.amount, line_total.amount), line_total.currency)


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

    def applies_to(self, item: CartItem) -> bool:
        return super().applies_to(item) and item.quantity >= self.min_quantity

    def calculate(self, item: CartItem) -> Money:
        if item.price.currency != self.amount.currency:
            raise CurrencyMismatchError(
                f"cannot mix {item.price.currency} and {self.amount.currency}"
            )
        line_total = item.line_total()
        return Money(min(self.amount.amount, line_total.amount), line_total.currency)
