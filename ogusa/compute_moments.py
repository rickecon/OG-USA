"""
This module uses data from FRED and other sources to compute data
moments that are used in the calibration of the OG-USA model.
"""

# imports
from fredapi import Fred
import os
import pandas as pd
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
    macro_moments[r"Interest rate $(r)$"] = (
        fred_data_d["BAA Corp Bond Rates"].mean() / 100
    )
    macro_moments[r"Capital share of output"] = (
        1 - fred_data_a["Labor share"].mean()
    )
    macro_moments[r"Labor share of output"] = fred_data_a["Labor share"].mean()

    return macro_moments


def get_fiscal_moments(year=2025):
    """
    Compute moments that use macro data.

    Computes the following moments:

        r"Revenue to GDP ratio $(T/Y)$"
        r"Gov't consumption to GDP ratio $(G/Y)$"
        r"Pension outlays to GDP ratio $(Pension/Y)$"
        r"Infrastructure spending to GDP ratio $(I_g/Y)$"
        r"Debt to GDP ratio $(D/Y)$"
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

    fiscal_moments[r"Revenue to GDP ratio $(T/Y)$"] = _mean_ratio(
        fred_data_q["Federal tax receipts"], fred_data_q["Nominal GDP"]
    )
    fiscal_moments[r"Debt to GDP ratio $(D/Y)$"] = _mean_ratio(
        fred_data_q["Debt held by public"], fred_data_q["Nominal GDP"]
    )
    gov_consumption = (
        fred_data_q["Gov expenditures"]
        - fred_data_q["Total gov transfer payments"]
        - fred_data_q["Gov interest payments"]
        - fred_data_q["Gov investment"]
    )
    fiscal_moments[r"Gov't consumption to GDP ratio $(G/Y)$"] = _mean_ratio(
        gov_consumption, fred_data_q["Nominal GDP"]
    )
    fiscal_moments[r"Pension outlays to GDP ratio $(Pension/Y)$"] = (
        _mean_ratio(
            fred_data_q["Social Security payments"], fred_data_q["Nominal GDP"]
        )
    )

    # find alpha_I
    fiscal_moments[r"Infrastructure spending to GDP ratio $(I_g/Y)$"] = (
        _mean_ratio(fred_data_q["Gov investment"], fred_data_q["Nominal GDP"])
    )

    return fiscal_moments
