
from app.risk.combined_risk_engine import (
    calculate_weighted_risk,
    classify_risk,
)


def test_combines_all_three_factors():
    factors = {
        "rainfall": {"available": True, "score": 80},
        "community_reports": {"available": True, "score": 75},
        "historical_floods": {"available": True, "score": 60},
    }

    result = calculate_weighted_risk(factors)

    assert result == 73.25


def test_renormalizes_when_rainfall_is_missing():
    factors = {
        "rainfall": {"available": False, "score": None},
        "community_reports": {"available": True, "score": 75},
        "historical_floods": {"available": True, "score": 60},
    }

    result = calculate_weighted_risk(factors)

    assert result == 68.75


def test_returns_none_when_all_factors_are_missing():
    factors = {
        "rainfall": {"available": False, "score": None},
        "community_reports": {"available": False, "score": None},
        "historical_floods": {"available": False, "score": None},
    }

    result = calculate_weighted_risk(factors)

    assert result is None


def test_rejects_invalid_score():
    factors = {
        "rainfall": {"available": True, "score": 150},
    }

    try:
        calculate_weighted_risk(factors)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_classifies_risk_levels():
    assert classify_risk(10) == "low"
    assert classify_risk(30) == "moderate"
    assert classify_risk(60) == "high"
    assert classify_risk(80) == "severe"
