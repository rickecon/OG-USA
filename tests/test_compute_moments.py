"""
Tests of compute_moments.py module.
"""

import numpy as np
import pandas as pd
import pytest
import zipfile

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
        index = pd.date_range(
            observation_start, observation_end, freq="MS"
        )
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


def _write_cps_zip(path, filename, rows):
    """
    Write a small CPS ASEC-like zip file for tests.
    """
    df = pd.DataFrame(rows)
    with zipfile.ZipFile(path, "w") as zip_file:
        zip_file.writestr(filename, df.to_csv(index=False))


def _write_psid_file(path):
    """
    Write a small PSID-like file for age profile tests.
    """
    psid = pd.DataFrame(
        {
            "age": [20, 21],
            "spouse_age": [0, 22],
            "head_annual_hours": [2000.0, 1600.0],
            "spouse_annual_hours": [0.0, 1000.0],
            "head_labor_inc": [50000.0, 60000.0],
            "spouse_labor_inc": [0.0, 20000.0],
            "head_noncorp_bus_labor_income": [1000.0, 2000.0],
            "spouse_noncorp_bus_labor_income": [0.0, 500.0],
            "food_out_expend": [10.0, 20.0],
            "food_in_expend": [1.0, 2.0],
        }
    )
    psid.to_csv(path, index=False)


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


def test_get_inequality_moments_returns_float_dict(monkeypatch):
    """
    Test that inequality moments are returned as a dictionary of floats.
    """
    from ogusa import wealth

    def income_ginis(income_year=None):
        return {
            "Gini coefficient, income": 0.4,
            "Gini coefficient, after-tax income": 0.35,
        }

    monkeypatch.setattr(
        compute_moments, "_taxcalc_cps_income_ginis", income_ginis
    )
    monkeypatch.setattr(
        wealth,
        "get_wealth_data",
        lambda *args, **kwargs: pd.DataFrame({"networth_infadj": [1.0]}),
    )
    monkeypatch.setattr(
        wealth,
        "compute_wealth_moments",
        lambda *args, **kwargs: np.array([1.0, 0.8, 2.0]),
    )

    moments = compute_moments.get_inequality_moments()

    _assert_float_dict(moments)


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


def test_get_age_profile_moments_hours_from_cps():
    """
    Test hours age profiles from a supplied CPS-like dataframe.
    """
    cps = pd.DataFrame(
        {
            "age": [20, 20, 21],
            "hours": [100.0, 200.0, 400.0],
            "wtsupp": [1.0, 3.0, 2.0],
        }
    )

    profile = compute_moments.get_age_profile_moments(
        "hours",
        min_age=20,
        max_age=22,
        cps=cps,
        psid_fallback=False,
    )

    assert len(profile) == 80
    assert profile.index[0] == 20
    assert profile.index[-1] == 99
    assert np.isclose(profile.loc[20], 175.0 / ((24 - 8) * 7))
    assert np.isclose(profile.loc[21], 400.0 / ((24 - 8) * 7))
    assert np.isnan(profile.loc[22])
    assert np.isnan(profile.loc[99])


def test_get_age_profile_moments_hours_from_nber_cps(tmp_path):
    """
    Test hours age profiles from pooled NBER CPS ASEC-like files.
    """
    cps_2023 = tmp_path / "asecpub23csv.zip"
    cps_2022 = tmp_path / "asecpub22csv.zip"
    _write_cps_zip(
        cps_2023,
        "pppub23.csv",
        [
            {"A_AGE": 20, "HRSWK": 40, "WKSWORK": 52, "A_FNLWGT": 1},
            {"A_AGE": 20, "HRSWK": 0, "WKSWORK": 0, "A_FNLWGT": 1},
        ],
    )
    _write_cps_zip(
        cps_2022,
        "pppub22.csv",
        [
            {"A_AGE": 20, "HRSWK": 20, "WKSWORK": 10, "A_FNLWGT": 2},
            {"A_AGE": 21, "HRSWK": 40, "WKSWORK": 1, "A_FNLWGT": 4},
        ],
    )

    profile = compute_moments.get_age_profile_moments(
        "hours",
        min_age=20,
        max_age=21,
        cps_years=(2023, 2022),
        cps_urls={2023: cps_2023, 2022: cps_2022},
    )

    assert len(profile) == 80
    assert np.isclose(profile.loc[20], 20.0 / ((24 - 8) * 7))
    assert np.isclose(profile.loc[21], 40.0 / ((24 - 8) * 7))
    assert np.isnan(profile.loc[22])
    assert np.isnan(profile.loc[99])


@pytest.mark.parametrize("var", ["earnings", "hours", "wealth", "consumption"])
def test_get_age_profile_moments_returns_length_80_series(var, tmp_path):
    """
    Test that every age-profile variable returns an 80-element Series.
    """
    psid_path = tmp_path / "psid.csv"
    _write_psid_file(psid_path)
    scf_dir = tmp_path / "SCF"
    scf_dir.mkdir()
    pd.DataFrame(
        {
            "age": [20, 21],
            "networth": [10000.0, 20000.0],
            "networth_infadj": [10000.0, 20000.0],
            "wgt": [1.0, 1.0],
        }
    ).to_csv(scf_dir / "scf_wealth_2019.csv", index=False)
    cps = pd.DataFrame(
        {
            "age": [20, 21],
            "hours": [20.0, 30.0],
            "weight": [1.0, 1.0],
        }
    )

    kwargs = {
        "earnings": {
            "earnings_source": "psid",
            "psid_path": psid_path,
        },
        "hours": {"cps": cps},
        "wealth": {
            "scf_yrs_list": [2019],
            "scf_directory": scf_dir,
        },
        "consumption": {"psid_path": psid_path},
    }

    profile = compute_moments.get_age_profile_moments(var, **kwargs[var])

    assert isinstance(profile, pd.Series)
    assert len(profile) == 80


def test_get_age_profile_moments_consumption_from_psid(tmp_path):
    """
    Test consumption age profiles from a supplied PSID-like file.
    """
    psid = pd.DataFrame(
        {
            "age": [20, 20, 21],
            "food_out_expend": [10.0, 20.0, 30.0],
            "food_in_expend": [1.0, 2.0, 3.0],
        }
    )
    psid_path = tmp_path / "psid.csv"
    psid.to_csv(psid_path, index=False)

    profile = compute_moments.get_age_profile_moments(
        "consumption",
        min_age=20,
        max_age=21,
        psid_path=psid_path,
    )

    assert len(profile) == 80
    assert np.isclose(profile.loc[20], 16.5)
    assert np.isclose(profile.loc[21], 33.0)
    assert np.isnan(profile.loc[22])
    assert np.isnan(profile.loc[99])


def test_get_age_profile_moments_invalid_var():
    """
    Test validation of the age-profile variable argument.
    """
    with pytest.raises(ValueError):
        compute_moments.get_age_profile_moments("bad_var")
