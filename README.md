# Discount Calculator

Applies fixed, percentage, and volume discounts to a shopping cart and returns the discounted total.

## Requirements

- Python **3.13+**
- [Poetry](https://python-poetry.org/) 2.x

## Getting started

```bash
make install        # install all dependencies
make check          # format-check + lint-check + types + test (full CI gate)
make format-fix     # ruff format — auto-reformat code
make format-check   # ruff format --check — verify formatting without changing files
make lint-fix       # ruff check --fix — lint and auto-apply safe fixes
make lint-check     # ruff check — style, imports, bugbear
make types          # mypy — strict type checking
make test           # pytest
```

## Usage

```python
from discount_calculator import (
    CartItem, Money, Percentage,
    DiscountCalculator, BestDiscountPolicy,
    FixedDiscount, PercentageDiscount, VolumeDiscount,
)

items = [
    CartItem(code="WIDGET", price=Money(1000, "EUR"), quantity=3),
]

calc = DiscountCalculator(
    discounts=[
        FixedDiscount(restricted_to=None, amount_per_unit=Money(200, "EUR")),
        PercentageDiscount(restricted_to=frozenset({"WIDGET"}), percentage=Percentage(1500)),
    ],
    policy=BestDiscountPolicy(),
)

total = calc.calculate_total(items)  # Money(amount=..., currency='EUR')
```

## Design notes

- Money amounts are in minor units — `Money(1000, "EUR")` is €10.00.
- `Percentage` takes basis points (1500 = 15%).
- At most one discount applies per cart line, governed by `DiscountPolicy`. `BestDiscountPolicy` is the default; swap it out to change the selection behaviour.
- All value objects are immutable (`frozen=True`).
