from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from discount_calculator.exceptions import InvalidPercentageError
from discount_calculator.money import Money


@dataclass(frozen=True)
class Percentage:
    basis_points: int

    def __post_init__(self) -> None:
        if not (0 <= self.basis_points <= 10000):
            raise InvalidPercentageError(
                f"basis_points must be in [0, 10000], got {self.basis_points}"
            )

    def apply_to(self, money: Money) -> Money:
        amount = int(
            (Decimal(money.amount) * Decimal(self.basis_points) / Decimal(10000))
            .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        return Money(amount, money.currency)
