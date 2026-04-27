from discount_calculator.cart_item import CartItem
from discount_calculator.discount_policy import DiscountPolicy
from discount_calculator.discounts import Discount
from discount_calculator.exceptions import EmptyCartError
from discount_calculator.money import Money


class DiscountCalculator:
    def __init__(self, discounts: list[Discount], policy: DiscountPolicy) -> None:
        self._discounts = discounts
        self._policy = policy

    def calculate_total(self, items: list[CartItem]) -> Money:
        if not items:
            raise EmptyCartError("cart must contain at least one item")

        total = Money(0, items[0].price.currency)
        for item in items:
            saving = self._policy.calculate(self._discounts, item)
            total = total + item.line_total() - saving
        return total
