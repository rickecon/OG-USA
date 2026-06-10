"""
This module uses data from FRED and other sources to compute data
moments that are used in the calibration of the OG-USA model.
"""

# imports
from fredapi import Fred
import os
import pandas as pd
import numpy as np
import datetime


def _mean_ratio(numerator, denominator):
    """
    Return the average of numerator / denominator over common observations.
    """
    ratio_data = pd.concat(
        [numerator.rename("numerator"), denominator.rename("denominator")],
        axis=1,
    ).dropna()
    return (ratio_data["numerator"] / ratio_data["denominator"]).mean()


def _ratio_moment(numerator, denominator, last_value_only=False):
    """
    Return either the last ratio or average ratio over common observations.
    """
    ratio_data = pd.concat(
        [numerator.rename("numerator"), denominator.rename("denominator")],
        axis=1,
    ).dropna()
    ratio = ratio_data["numerator"] / ratio_data["denominator"]
    if last_value_only:
        return ratio.iloc[-1]
    return ratio.mean()


def _mean_real_rate(nominal_rate, price_index):
    """
    Return the average nominal rate less inflation over common observations.
    """
    nominal_rate_a = nominal_rate.resample("YE").mean() / 100
    inflation = price_index.pct_change()
    rate_data = pd.concat(
        [
            nominal_rate_a.rename("nominal_rate"),
            inflation.rename("inflation"),
        ],
        axis=1,
    ).dropna()
    return (rate_data["nominal_rate"] - rate_data["inflation"]).mean()


def _weighted_gini(values, weights):
    """
    Compute the weighted Gini coefficient.
    """
    data = pd.DataFrame({"value": values, "weight": weights})
    data = data.replace([np.inf, -np.inf], np.nan).dropna()
    data = data[data["weight"] > 0].copy()
    if data.empty:
        raise ValueError("No observations with positive weight.")

    data.sort_values(by="value", ascending=True, inplace=True)
    weighted_value = data["value"] * data["weight"]
    total_weighted_value = weighted_value.sum()
    if np.isclose(total_weighted_value, 0.0):
        raise ValueError("Weighted sum of values is zero.")

    p = (data["weight"].cumsum() / data["weight"].sum()).values
    nu = (weighted_value.cumsum() / total_weighted_value).values
    return float((nu[1:] * p[:-1]).sum() - (nu[:-1] * p[1:]).sum())


def _taxcalc_cps_income_ginis(income_year=None):
    """
    Compute income Ginis from Tax-Calculator CPS records.
    """
    from taxcalc import Calculator, Policy, Records

    calc = Calculator(records=Records.cps_constructor(), policy=Policy())
    if income_year is not None:
        calc.advance_to_year(income_year)
    calc.calc_all()

    weights = calc.array("s006")
    before_tax_income = calc.array("expanded_income") - calc.array(
        "benefit_value_total"
    )
    after_tax_income = calc.array("aftertax_income")

    return {
        "Gini coefficient, income": _weighted_gini(
            before_tax_income, weights
        ),
        "Gini coefficient, after-tax income": _weighted_gini(after_tax_income, weights),
    }


def _convert_nominal_to_base_year(nominal, deflator, base_year):
    """
    Convert nominal dollars to dollars in the deflator's base-year prices.
    """
    base_date = pd.Timestamp(base_year, 12, 31)
    base_deflator = deflator.loc[base_date]
    return nominal * base_deflator / deflator


def get_macro_moments(year=2025):
    """
    Compute moments that use macro data.

    Computes the following moments:

        r"Investment rate $(I/K)$",
        r"Capital-Output ratio $(K/Y)$",
        r"Consumption-Output ratio $(C/Y)$",
        r"Savings rate $(B/Y)$",
        r"Interest rate $(r)$",
        r"Capital share of output",
        r"Labor share of output",
    """

    # set beginning and end dates for data
    # format is year (1940),month (1),day (1)
    start = datetime.datetime(1947, 1, 1)
    end = min(datetime.date.today(), datetime.date(year, 12, 31))
    # Deflator conversion uses 2021 prices even if the ratio sample ends
    # earlier.
    observation_end = max(end, datetime.date(2021, 12, 31))

    variable_dict = {
        "GDP Per Capita": "A939RX0Q048SBEA",
        "Labor share": "LABSHPUSA156NRUG",
        "Debt held by foreigners": "FDHBFIN",
        "Debt held by public": "FYGFDPUN",
        "BAA Corp Bond Rates": "DBAA",
        "10 year treasury rate": "DGS10",
        "Total gov transfer payments": "B087RC1Q027SBEA",
        "Social Security payments": "W823RC1",
        "Gov expenditures": "FGEXPND",
        "Gov investment": "A782RC1Q027SBEA",
        "Gov interest payments": "A091RC1Q027SBEA",
        "Real GDP": "GDPC1",
        "Nominal GDP": "GDP",
        "Fixed private investment": "FPI",
        "Personal consumption expenditures": "PCE",
        "Gross private savings": "GPSAVE",
        "Real capital stock": "RKNANPUSA666NRUG",  # 2021 dollars, in millions
        "GDP deflator": "A191RD3A086NBEA",  # 2017 = 100
        "Fixed private investment deflator": "A007RD3A086NBEA",  # 2017 = 100
    }

    # pull series of interest using fredapi
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise ValueError(
            "FRED_API_KEY environment variable is not set. "
            "A free API key can be obtained at "
            "https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    fred = Fred(api_key=api_key)
    series_list = []
    for name, series_id in variable_dict.items():
        s = fred.get_series(
            series_id, observation_start=start, observation_end=observation_end
        )
        s.name = name
        series_list.append(s)
    fred_data = pd.concat(series_list, axis=1)
    fred_data_common = fred_data.loc[: pd.Timestamp(end)].copy()

    # make sure all dollar value data are in billions
    fred_data_common["Debt held by public"] = (
        fred_data_common["Debt held by public"] / 1000
    )

    # Separate quarterly, monthly, and annual data series
    fred_data_q = (
        fred_data_common[
            [
                "Debt held by public",
                "Nominal GDP",
                "Real GDP",
                "Total gov transfer payments",
                "Social Security payments",
                "Gov expenditures",
                "Gov investment",
                "Gov interest payments",
                "GDP Per Capita",
                "Fixed private investment",
                "Personal consumption expenditures",
                "Gross private savings",
            ]
        ]
        .resample("QE")
        .mean()
    )
    fred_data_a = (
        fred_data_common[
            [
                "Labor share",
                "Real capital stock",
                "GDP deflator",
                "Fixed private investment deflator",
            ]
        ]
        .resample("YE")
        .mean()
    )
    fred_data_d = fred_data_common[
        ["BAA Corp Bond Rates", "10 year treasury rate"]
    ]
    fred_data_a_all = (
        fred_data[
            ["GDP deflator", "Fixed private investment deflator"]
        ]
        .resample("YE")
        .mean()
    )

    # Convert quarterly flow series to annual frequency for stock-flow ratios.
    fred_data_qa = fred_data_q.resample("YE").mean()
    capital_stock_billions = fred_data_a["Real capital stock"] / 1000
    fixed_private_investment_2021 = _convert_nominal_to_base_year(
        fred_data_qa["Fixed private investment"],
        fred_data_a_all["Fixed private investment deflator"],
        2021,
    )
    real_gdp_2021 = fred_data_qa["Real GDP"] * (
        fred_data_a_all["GDP deflator"].loc[pd.Timestamp(2021, 12, 31)] / 100
    )

    macro_moments = {}
    macro_moments[r"Investment rate $(I/K)$"] = (
        _mean_ratio(fixed_private_investment_2021, capital_stock_billions)
    )
    macro_moments[r"Capital-Output ratio $(K/Y)$"] = _mean_ratio(
        capital_stock_billions, real_gdp_2021
    )
    macro_moments[r"Consumption-Output ratio $(C/Y)$"] = _mean_ratio(
        fred_data_q["Personal consumption expenditures"],
        fred_data_q["Nominal GDP"],
    )
    macro_moments[r"Savings rate $(B/Y)$"] = _mean_ratio(
        fred_data_q["Gross private savings"], fred_data_q["Nominal GDP"]
    )
    macro_moments[r"Interest rate $(r)$"] = _mean_real_rate(
        fred_data_d["BAA Corp Bond Rates"], fred_data_a["GDP deflator"]
    )
    macro_moments[r"Capital share of output"] = (
        1 - fred_data_a["Labor share"].mean()
    )
    macro_moments[r"Labor share of output"] = fred_data_a["Labor share"].mean()

    return macro_moments


def get_fiscal_moments(year=2025, last_value_only=True):
    """
    Compute moments that use macro data.

    Computes the following moments:

        r"Revenue to GDP ratio $(T/Y)$"
        r"Gov't consumption to GDP ratio $(G/Y)$"
        r"Pension outlays to GDP ratio $(Pension/Y)$"
        r"Infrastructure spending to GDP ratio $(I_g/Y)$"
        r"Debt to GDP ratio $(D/Y)$"

    Args:
        year (int): Inclusive end year for FRED data.
        last_value_only (bool): If True, use the last common ratio
            observation. If False, use the mean ratio over all common
            observations.
    """

    # set beginning and end dates for data
    # format is year (1940),month (1),day (1)
    start = datetime.datetime(1947, 1, 1)
    end = min(datetime.date.today(), datetime.date(year, 12, 31))

    variable_dict = {
        "GDP Per Capita": "A939RX0Q048SBEA",
        "Labor share": "LABSHPUSA156NRUG",
        "Debt held by foreigners": "FDHBFIN",
        "Debt held by public": "FYGFDPUN",
        "BAA Corp Bond Rates": "DBAA",
        "10 year treasury rate": "DGS10",
        "Total gov transfer payments": "B087RC1Q027SBEA",
        "Social Security payments": "W823RC1",
        "Gov expenditures": "FGEXPND",
        "Gov investment": "A782RC1Q027SBEA",
        "Gov interest payments": "A091RC1Q027SBEA",
        "Real GDP": "GDPC1",
        "Nominal GDP": "GDP",
        "Fixed private investment": "FPI",
        "Personal consumption expenditures": "PCE",
        "Gross private savings": "GPSAVE",
        "Federal tax receipts": "W006RC1Q027SBEA",
    }

    # pull series of interest using fredapi
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise ValueError(
            "FRED_API_KEY environment variable is not set. "
            "A free API key can be obtained at "
            "https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    fred = Fred(api_key=api_key)
    series_list = []
    for name, series_id in variable_dict.items():
        s = fred.get_series(
            series_id, observation_start=start, observation_end=end
        )
        s.name = name
        series_list.append(s)
    fred_data = pd.concat(series_list, axis=1)

    # make sure all dollar value data are in billions
    fred_data["Debt held by public"] = fred_data["Debt held by public"] / 1000

    # Separate quarterly, monthly, and annual data series
    fred_data_q = (
        fred_data[
            [
                "Debt held by public",
                "Nominal GDP",
                "Total gov transfer payments",
                "Social Security payments",
                "Gov expenditures",
                "Gov investment",
                "Gov interest payments",
                "GDP Per Capita",
                "Federal tax receipts",
            ]
        ]
        .resample("QE")
        .mean()
    )

    # initialize a dictionary of parameters
    fiscal_moments = {}

    fiscal_moments[r"Revenue to GDP ratio $(T/Y)$"] = _ratio_moment(
        fred_data_q["Federal tax receipts"],
        fred_data_q["Nominal GDP"],
        last_value_only,
    )
    fiscal_moments[r"Debt to GDP ratio $(D/Y)$"] = _ratio_moment(
        fred_data_q["Debt held by public"],
        fred_data_q["Nominal GDP"],
        last_value_only,
    )
    gov_consumption = (
        fred_data_q["Gov expenditures"]
        - fred_data_q["Total gov transfer payments"]
        - fred_data_q["Gov interest payments"]
        - fred_data_q["Gov investment"]
    )
    fiscal_moments[r"Gov't consumption to GDP ratio $(G/Y)$"] = (
        _ratio_moment(
            gov_consumption, fred_data_q["Nominal GDP"], last_value_only
        )
    )
    fiscal_moments[r"Pension outlays to GDP ratio $(Pension/Y)$"] = (
        _ratio_moment(
            fred_data_q["Social Security payments"],
            fred_data_q["Nominal GDP"],
            last_value_only,
        )
    )

    # find alpha_I
    fiscal_moments[r"Infrastructure spending to GDP ratio $(I_g/Y)$"] = (
        _ratio_moment(
            fred_data_q["Gov investment"],
            fred_data_q["Nominal GDP"],
            last_value_only,
        )
    )

    return fiscal_moments


def get_demographic_moments(p, demographic_data_path=None):
    """
    Compute moments that use demographic data.

    Computes the following moments:

        r"Fraction 65+"
        r"Pop growth rate"

    Args:
        p (OG-Core Specifications object): model parameters.
        demographic_data_path (str): path to save downloaded demographic data.
    """
    from ogcore import demographics

    pop_objs = demographics.get_pop_objs(
        p.E,
        p.S,
        p.T,
        0,
        99,
        initial_data_year=p.start_year - 1,
        final_data_year=p.start_year,
        GraphDiag=False,
        download_path=demographic_data_path,
    )

    ages = np.arange(p.E, p.E + p.S)
    omega = pop_objs["omega"][0, :]

    demographic_moments = {}
    demographic_moments[r"Fraction 65+"] = float(omega[ages >= 65].sum())
    demographic_moments[r"Pop growth rate"] = float(pop_objs["g_n"][0])

    return demographic_moments


def get_inequality_moments(
    income_source="cps",
    wealth_source="scf",
    income_year=None,
    scf_yrs_list=None,
    scf_web=True,
    scf_directory=None,
):
    """
    Compute moments that use income and wealth microdata.

    Computes the following moments:

        r"Before-tax income Gini"
        r"After-tax income Gini"
        r"Wealth Gini"

    Args:
        income_source (str): Source for income data. Currently supports
            "cps".
        wealth_source (str): Source for wealth data. Currently supports
            "scf".
        income_year (int): Year to use for Tax-Calculator CPS records. If
            None, use the CPS data start year.
        scf_yrs_list (list): SCF survey years to pool. If None, use the
            default years in wealth.get_wealth_data().
        scf_web (bool): If True, download SCF data from the web.
        scf_directory (str): Local SCF data directory when scf_web=False.
    """
    inequality_moments = {}
    income_source = income_source.lower()
    wealth_source = wealth_source.lower()

    if income_source == "cps":
        inequality_moments.update(_taxcalc_cps_income_ginis(income_year))
    else:
        raise ValueError(f"Unsupported income data source: {income_source}")

    if wealth_source == "scf":
        from ogusa import wealth

        if scf_yrs_list is None:
            scf = wealth.get_wealth_data(web=scf_web, directory=scf_directory)
        else:
            scf = wealth.get_wealth_data(
                scf_yrs_list=scf_yrs_list,
                web=scf_web,
                directory=scf_directory,
            )
        wealth_moments = wealth.compute_wealth_moments(
            scf.copy(), np.array([1.0])
        )
        inequality_moments["Gini coefficient, wealth"] = float(wealth_moments[-2])
    else:
        raise ValueError(f"Unsupported wealth data source: {wealth_source}")

    return inequality_moments
