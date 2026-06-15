"""
This module uses data from FRED to find values for parameters for the
OG-USA model that rely on macro data for calibration.
"""

# imports
from fredapi import Fred
import os
import pandas as pd
import numpy as np
import datetime
import statsmodels.api as sm


def get_macro_params():
    """
    Compute values of parameters that are derived from macro data
    """

    # set beginning and end dates for data
    # format is year (1940),month (1),day (1)
    start = datetime.datetime(1947, 1, 1)
    end = datetime.date.today()  # go through today
    baseline_date = datetime.datetime(2025, 12, 31)

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
            ]
        ]
        .resample("QE")
        .mean()
    )
    fred_data_a = fred_data[["Labor share"]]
    fred_data_d = fred_data[["BAA Corp Bond Rates", "10 year treasury rate"]]

    # initialize a dictionary of parameters
    macro_parameters = {}

    # print(fred_data.loc(str(baseline_date)))
    # find initial_debt_ratio
    macro_parameters["initial_debt_ratio"] = pd.Series(
        fred_data_q["Debt held by public"] / fred_data_q["Nominal GDP"]
    ).loc[baseline_date]

    # find alpha_T
    macro_parameters["alpha_T"] = pd.Series(
        (
            fred_data_q["Total gov transfer payments"]
            - fred_data_q["Social Security payments"]
        )
        / fred_data_q["Nominal GDP"]
    ).loc[baseline_date]

    # find alpha_G
    macro_parameters["alpha_G"] = pd.Series(
        (
            fred_data_q["Gov expenditures"]
            - fred_data_q["Total gov transfer payments"]
            - fred_data_q["Gov interest payments"]
            - fred_data_q["Gov investment"]
        )
        / fred_data_q["Nominal GDP"]
    ).loc[baseline_date]

    # find alpha_I
    macro_parameters["alpha_I"] = pd.Series(
        fred_data_q["Gov investment"] / fred_data_q["Nominal GDP"]
    ).loc[baseline_date]

    # find gamma
    macro_parameters["gamma"] = 1 - fred_data_a["Labor share"].mean()

    # find g_y
    macro_parameters["g_y"] = (
        fred_data_q["GDP Per Capita"]
        .pct_change(periods=4, freq="QE", fill_method=None)
        .mean()
    )

    # # estimate r_gov_shift and r_gov_scale
    rate_data = (
        (
            fred_data_d[
                ["10 year treasury rate", "BAA Corp Bond Rates"]
            ].dropna()[-50:]
        )
        / 100
    )  # divide by 100 bc data in percentage points
    rate_data["constant"] = np.ones(len(rate_data.index))
    mod = sm.OLS(
        rate_data["10 year treasury rate"],
        rate_data[["constant", "BAA Corp Bond Rates"]],
    )
    res = mod.fit()
    macro_parameters["r_gov_scale"] = res.params["BAA Corp Bond Rates"]
    macro_parameters["r_gov_shift"] = res.params["constant"] * -1

    return macro_parameters
