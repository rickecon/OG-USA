"""
Tests of compute_moments.py module.
"""

import numpy as np
import pandas as pd
import pytest

from ogusa import compute_moments


def _assert_float_dict(moment_dict):
    """
    Assert that a moment dictionary has only float values.
    """
    assert isinstance(moment_dict, dict)
    assert moment_dict
    for value in moment_dict.values():
        assert isinstance(value, (float, np.floating))


class MockFred:
    """
    Minimal fredapi.Fred replacement for macro and fiscal moment tests.
    """

    values = {
        "A191RD3A086NBEA": 100.0,
        "A007RD3A086NBEA": 100.0,
        "LABSHPUSA156NRUG": 0.6,
        "DBAA": 5.0,
        "DGS10": 3.0,
        "RKNANPUSA666NRUG": 100000.0,
        "FYGFDPUN": 100000.0,
    }

    def __init__(self, api_key):
        self.api_key = api_key

    def get_series(self, series_id, observation_start, observation_end):
        """
        Return a deterministic monthly series for any requested FRED ID.
        """
        index = pd.date_range(observation_start, observation_end, freq="MS")
        value = self.values.get(series_id, 1000.0)
        return pd.Series(value, index=index, dtype=float)


class MockParams:
    """
    Minimal OG-Core parameters object for demographic moment tests.
    """

    E = 20
    S = 80
    T = 320
    start_year = 2026


def test_get_macro_moments_returns_float_dict(monkeypatch):
    """
    Test that macro moments are returned as a dictionary of floats.
    """
    monkeypatch.setenv("FRED_API_KEY", "test-key")
    monkeypatch.setattr(compute_moments, "Fred", MockFred)

    moments = compute_moments.get_macro_moments(year=2021)

    _assert_float_dict(moments)


def test_get_fiscal_moments_returns_float_dict(monkeypatch):
    """
    Test that fiscal moments are returned as a dictionary of floats.
    """
    monkeypatch.setenv("FRED_API_KEY", "test-key")
    monkeypatch.setattr(compute_moments, "Fred", MockFred)

    moments = compute_moments.get_fiscal_moments(year=2021)

    _assert_float_dict(moments)


def test_get_inequality_moments_returns_float_dict():
    """
    Test that inequality moments are returned as a dictionary of floats.
    """
    moments = compute_moments.get_inequality_moments(scf_yrs_list=[2019])

    _assert_float_dict(moments)
    assert set(moments) == {
        "Gini coefficient, income",
        "Gini coefficient, after-tax income",
        "Gini coefficient, wealth",
    }
    for value in moments.values():
        assert 0.0 <= value <= 1.0


def test_get_demographic_moments_returns_float_dict(monkeypatch):
    """
    Test that demographic moments are returned as a dictionary of floats.
    """
    from ogcore import demographics

    def get_pop_objs(*args, **kwargs):
        return {
            "omega": np.ones((1, MockParams.S)) / MockParams.S,
            "g_n": np.array([0.01]),
        }

    monkeypatch.setattr(demographics, "get_pop_objs", get_pop_objs)

    moments = compute_moments.get_demographic_moments(MockParams())

    _assert_float_dict(moments)


@pytest.mark.parametrize("var", ["earnings", "hours", "wealth", "consumption"])
def test_get_age_profile_moments_returns_length_80_series(var):
    """
    Test every age-profile variable using packaged survey data.
    """
    kwargs = {
        "earnings": {"earnings_source": "psid"},
        "hours": {},
        "wealth": {},
        "consumption": {},
    }

    profile = compute_moments.get_age_profile_moments(var, **kwargs[var])

    assert isinstance(profile, pd.Series)
    assert len(profile) == 80


def test_get_age_profile_moments_consumption_from_packaged_psid():
    """
    Test consumption age profiles from packaged PSID data.
    """
    profile = compute_moments.get_age_profile_moments(
        "consumption", min_age=20, max_age=21
    )

    assert len(profile) == 80
    assert np.isfinite(profile.loc[20])
    assert np.isfinite(profile.loc[21])
    assert np.isnan(profile.loc[22])
    assert np.isnan(profile.loc[99])


def test_get_age_profile_moments_invalid_var():
    """
    Test validation of the age-profile variable argument.
    """
    with pytest.raises(ValueError):
        compute_moments.get_age_profile_moments("bad_var")
