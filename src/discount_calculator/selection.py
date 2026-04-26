from __future__ import annotations

from abc import ABC, abstractmethod

from discount_calculator.cart_item import CartItem
from discount_calculator.discounts import Discount


class DiscountSelector(ABC):
    @abstractmethod
    def select(self, discounts: list[Discount], item: CartItem) -> Discount | None: ...


class BestDiscountSelector(DiscountSelector):
    def select(self, discounts: list[Discount], item: CartItem) -> Discount | None:
        best_discount: Discount | None = None
        best_saving: int = -1
        for discount in discounts:
            if not discount.applies_to(item):
                continue
            saving = discount.calculate(item).amount
            if saving > best_saving:
                best_discount = discount
                best_saving = saving
        return best_discount
