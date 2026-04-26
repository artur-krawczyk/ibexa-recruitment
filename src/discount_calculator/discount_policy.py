from __future__ import annotations

from abc import ABC, abstractmethod

from discount_calculator.cart_item import CartItem
from discount_calculator.discounts import Discount
from discount_calculator.money import Money


class DiscountPolicy(ABC):
    @abstractmethod
    def calculate(self, discounts: list[Discount], item: CartItem) -> Money: ...


class BestDiscountPolicy(DiscountPolicy):
    def calculate(self, discounts: list[Discount], item: CartItem) -> Money:
        best_saving = 0
        for discount in discounts:
            if not discount.applies_to(item):
                continue
            saving = discount.calculate(item).amount
            if saving > best_saving:
                best_saving = saving
        return Money(best_saving, item.price.currency)
