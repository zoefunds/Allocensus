import pytest
from app.utils.constraints import validate_portfolio_constraints


def test_valid_portfolio():
    allocations = {"BTC": 25.0, "ETH": 20.0, "USDC": 10.0, "AAPL": 20.0, "GOLD": 25.0}
    asset_classes = {"BTC": "cryptocurrencies", "ETH": "cryptocurrencies", "USDC": "stablecoins", "AAPL": "equities", "GOLD": "commodities"}
    violations = validate_portfolio_constraints(allocations, asset_classes)
    assert violations == [], f"Expected no violations but got: {violations}"


def test_single_asset_too_high():
    allocations = {"BTC": 35.0, "ETH": 15.0, "USDC": 10.0, "AAPL": 20.0, "GOLD": 20.0}
    asset_classes = {"BTC": "cryptocurrencies", "ETH": "cryptocurrencies", "USDC": "stablecoins", "AAPL": "equities", "GOLD": "commodities"}
    violations = validate_portfolio_constraints(allocations, asset_classes)
    rules = [v.rule for v in violations]
    assert "MAX_SINGLE_ASSET" in rules


def test_insufficient_liquidity():
    allocations = {"BTC": 30.0, "ETH": 25.0, "AAPL": 25.0, "GOLD": 20.0}
    asset_classes = {"BTC": "cryptocurrencies", "ETH": "cryptocurrencies", "AAPL": "equities", "GOLD": "commodities"}
    violations = validate_portfolio_constraints(allocations, asset_classes)
    rules = [v.rule for v in violations]
    assert "MIN_LIQUIDITY" in rules


def test_too_few_asset_classes():
    allocations = {"BTC": 50.0, "ETH": 45.0, "USDC": 5.0}
    asset_classes = {"BTC": "cryptocurrencies", "ETH": "cryptocurrencies", "USDC": "stablecoins"}
    violations = validate_portfolio_constraints(allocations, asset_classes)
    rules = [v.rule for v in violations]
    assert "MIN_DIVERSIFICATION" in rules


def test_no_leverage():
    allocations = {"BTC": 105.0, "USDC": -5.0, "ETH": 0.0}
    asset_classes = {"BTC": "cryptocurrencies", "USDC": "stablecoins", "ETH": "cryptocurrencies"}
    violations = validate_portfolio_constraints(allocations, asset_classes)
    rules = [v.rule for v in violations]
    assert "NO_LEVERAGE" in rules
