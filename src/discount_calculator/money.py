from __future__ import annotations

from dataclasses import dataclass

from discount_calculator.exceptions import CurrencyMismatchError, InvalidMoneyError


@dataclass(frozen=True)
class Money:
    amount: int
    currency: str

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise InvalidMoneyError(f"amount must be an int, got {type(self.amount).__name__}")
        if self.amount < 0:
            raise InvalidMoneyError(f"amount must be non-negative, got {self.amount}")
        if not self.currency:
            raise InvalidMoneyError("currency must be a non-empty string")

    def __add__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(max(self.amount - other.amount, 0), self.currency)

    def __mul__(self, n: int) -> Money:
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise InvalidMoneyError(f"multiplier must be a non-negative int, got {n!r}")
        return Money(self.amount * n, self.currency)

    def __lt__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.amount < other.amount

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(f"cannot mix {self.currency} and {other.currency}")
