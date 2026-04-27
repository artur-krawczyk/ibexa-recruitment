from abc import ABC, abstractmethod

from discount_calculator.cart_item import CartItem
from discount_calculator.discounts import Discount
from discount_calculator.money import Money


class DiscountPolicy(ABC):
    @abstractmethod
    def calculate(self, discounts: list[Discount], item: CartItem) -> Money: ...


class BestDiscountPolicy(DiscountPolicy):
    def calculate(self, discounts: list[Discount], item: CartItem) -> Money:
        best_saving = Money(0, item.price.currency)
        for discount in discounts:
            if not discount.applies_to(item):
                continue
            saving = discount.calculate(item)
            if best_saving < saving:
                best_saving = saving
        return best_saving
