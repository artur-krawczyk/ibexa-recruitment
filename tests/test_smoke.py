"""Phase 0 smoke test: confirms the package imports and pytest runs."""

import discount_calculator


def test_package_imports() -> None:
    assert hasattr(discount_calculator, "__all__")
