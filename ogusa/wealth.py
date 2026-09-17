import os
import datetime
import io
import zipfile
import numpy as np
import pandas as pd
import urllib.error
import urllib.request
from ogcore import utils as ogcore_utils
from ogusa import utils as ogusa_utils

# Set paths
CUR_PATH = os.path.split(os.path.abspath(__file__))[0]
CUR_DIR = os.path.dirname(os.path.realpath(__file__))
scf_data_dir = os.path.abspath(os.path.join(CUR_DIR, "data", "SCF"))

# Set some global parameters
scf_url = "https://www.federalreserve.gov/econres/files/scfp{year}s.zip"
scf_headers = {"User-Agent": "Mozilla/5.0"}
MIN_AGE, MAX_AGE = 21, 100
DIST_AGE_BIN_WIDTH = 10  # age bins for the output wealth distributions
# OG-Core default lifetime income group population shares
scf_default_lambdas = np.array([0.25, 0.25, 0.2, 0.1, 0.1, 0.09, 0.01])

# Define functions


def find_recent_scf_vintages(
    num_vintages=2, first_scf_year=1989, scf_url=scf_url, headers=scf_headers
):
    """
    Return the years of the most recent SCF vintages available on the
    Federal Reserve website, newest first.
    """
    this_year = datetime.date.today().year
    latest = this_year - (this_year - first_scf_year) % 3
    years = []
    for year in range(latest, first_scf_year - 1, -3):
        if ogusa_utils._url_exists(
            scf_url.format(year=year), headers=headers
        ):
            years.append(year)
        if len(years) == num_vintages:
            break
    return years


def load_scf(
    year, web=False, data_dir=scf_data_dir, scf_url=scf_url,
    headers=scf_headers
):
    """
    Download (or read the cached copy of) the SCF summary extract for a
    given survey year and return it as a DataFrame.
    """
    zip_path = os.path.join(data_dir, f"scfp{year}s.zip")
    if web:
        os.makedirs(data_dir, exist_ok=True)
        if not os.path.exists(zip_path):
            print(f"Downloading SCF {year} summary extract...")
            request = urllib.request.Request(
                scf_url.format(year=year), headers=headers
            )
            with urllib.request.urlopen(request, timeout=300) as response:
                with open(zip_path, "wb") as f:
                    f.write(response.read())
    with zipfile.ZipFile(zip_path) as zf:
        dta_name = [n for n in zf.namelist() if n.endswith(".dta")][0]
        df = pd.read_stata(io.BytesIO(zf.read(dta_name)))
    df.columns = df.columns.str.lower()
    return df


def compute_wealth_var(
    df_scf, foreign_equity_share=0.0, foreign_bond_share=0.0,
    exclude_durables=False
):
    """
    Add columns for domestic government debt holdings (D_d), domestic
    private asset holdings (K_d), and their sum (wealth) to the DataFrame.
    """
    df = df_scf.copy()
    gov_debt = (
        df["savbnd"] + df["govtbnd"] + df["notxbnd"] +
        df["gbmutf"] + df["tfbmutf"]
    )
    # EQUITY counts half of combination funds as equity, so the other half
    # is counted as bonds here
    foreign = foreign_equity_share * df["equity"] + foreign_bond_share * (
        df["obnd"] + df["obmutf"] + 0.5 * df["comutf"]
    )
    wealth = df["networth"] - foreign
    if exclude_durables:
        wealth = wealth - df["vehic"] - df["othnfin"]
    df["D_d"] = gov_debt
    df["K_d"] = wealth - gov_debt
    df["wealth"] = wealth
    return df


def assign_lifetime_income_group(
    df_scf, min_age=21, age_bin_width=5, lambdas=scf_default_lambdas
):
    """
    Assign each household to lifetime income group j = 0, ..., J-1 by its
    weighted percentile of normal income within its age bin.
    """
    df = df_scf.copy()
    # Drop all observations with df["age"] < min_age
    df = df[df["age"] >= min_age]
    df["age_bin"] = (df["age"] - min_age) // age_bin_width
    cutoffs = np.cumsum(lambdas)[:-1]
    df["j"] = 0
    for _, group in df.groupby("age_bin"):
        group = group.sort_values("norminc", kind="mergesort")
        weights = group["wgt"].to_numpy()
        pctile = (np.cumsum(weights) - 0.5 * weights) / weights.sum()
        df.loc[group.index, "j"] = np.searchsorted(
            cutoffs, pctile, side="right"
        )
    return df


def merge_infladj_mult_scf_years(df_scf_list, scf_years):
    """
    Consolidate multiple SCF years DataFrames into a single DataFrame, and
    adding inflation adjusted variables for D_d, K_d, and wealth to most recent
    CPILFESL monthly price levels.
    """
    df_cpi = ogusa_utils.get_cpi_monthly_data(start_year=min(scf_years))
    # Set cpi_cur to be the final monthly CPI value in df_cpi
    cpi_cur = df_cpi["CPILFESL"].iloc[-1]
    print("cpi_cur =", cpi_cur)
    df_scf_mult_year = pd.DataFrame()
    for year, df_scf in zip(scf_years, df_scf_list):
        df_scf["year"] = year
        # df_cpi["date"] holds "%Y-%m-%d" strings, so match July directly
        cpi_scf_year = (
            df_cpi.loc[df_cpi["date"] == f"{year}-07-01", "CPILFESL"]
        ).item()
        print("cpi_scf_year =", cpi_scf_year)
        df_scf["D_d_infladj"] = df_scf["D_d"] * (cpi_cur / cpi_scf_year)
        df_scf["K_d_infladj"] = df_scf["K_d"] * (cpi_cur / cpi_scf_year)
        df_scf["wealth_infladj"] = df_scf["wealth"] * (cpi_cur / cpi_scf_year)
        df_scf_mult_year = pd.concat(
            [df_scf_mult_year, df_scf], ignore_index=True
        )
    return df_scf_mult_year


def wealth_distributions(
    df, min_age=21, max_age=100, age_bin_width=10, lambdas=scf_default_lambdas
):
    """
    Return the share of total wealth held by households by  age bin
    of the head of household and lifetime income group j as an
    (age bins x J) DataFrame, an (age bins,) Series by age bin, and a
    (J,) Series by lifetime income group.
    """
    age_bin_starts = range(min_age, max_age + 1, age_bin_width)
    age_labels = [f"{a}-{a + age_bin_width - 1}" for a in age_bin_starts]
    age_bin = (df["age"] - min_age) // age_bin_width
    w_wealth = df["wgt"] * df["wealth_infladj"]
    # Group the Series by the two key Series directly. Adding the keys as
    # columns instead would copy the (already fragmented) input DataFrame.
    cell_wealth = (
        w_wealth.groupby([age_bin, df["j"]]).sum().unstack(fill_value=0.0)
    )
    dist_2d = (
        cell_wealth.reindex(
            index=range(len(age_labels)),
            columns=range(len(lambdas)),
            fill_value=0.0,
        )
        / w_wealth.sum()
    )
    dist_2d.index = pd.Index(age_labels, name="age")
    dist_2d.columns = pd.Index(
        [f"j={j}" for j in dist_2d.columns], name="lifetime income group"
    )
    # dist_2d rows are age bins and columns are lifetime income groups, so
    # summing across the columns (axis=1) marginalizes to age bins and
    # summing down the rows (axis=0) marginalizes to lifetime income groups.
    dist_sj = dist_2d
    dist_s = dist_2d.sum(axis=1)
    dist_j = dist_2d.sum(axis=0)
    return dist_sj, dist_s, dist_j


def get_wealth_data(
    scf_yrs_list=[2022, 2019, 2016, 2013, 2010, 2007],
    web=False,
    directory=None,
    include_age=False,
    scf_data_dir=scf_data_dir
):
    """
    Reads wealth data from the 2007, 2010, 2013, 2016, 2019, and 2022 Survey of
    Consumer Finances (SCF) files.

    Args:
        scf_yrs_list (list): list of SCF years to import. Currently the
            largest set of years that will work is
            [2022, 2019, 2016, 2013, 2010, 2007]
        web (Boolean): =True if function retrieves data from internet.
            Defaults to False and uses local trimmed CSVs in ogusa/data/SCF.
        directory (string or None): local directory location if data are
            stored on local drive, not use internet (web=False)
        include_age (Boolean): =True if function keeps the respondent age
            from the SCF summary extract.


    Returns:
        df_scf (Pandas DataFrame): pooled cross-sectional data from SCFs

    """
    # Hard code cpi list for given years. Index values are annual average index
    # values from monthly FRED Consumer Price Index for All Urban Consumers:
    # All Items Less Food and Energy in U.S. City Average (CPILFESL,
    # https://fred.stlouisfed.org/series/CPILFESL). Base year is 1982-1984=100.
    # Values are taken from the July numbers in 2022, 2019, 2016, 2013, 2010,
    # and 2007 [295.088, 263.280, 247.829, 233.880, 221.363, 210.773].
    # We then reset the base year to 2019 by dividing each annual average by
    # the 2019 annual average and multiply by 100. Base year is 2019=100
    cpi_dict = {
        "cpi2022": 100.000,
        "cpi2019": 89.2208426,
        "cpi2016": 83.98477742,
        "cpi2013": 79.25771295,
        "cpi2010": 75.01592745,
        "cpi2007": 71.42716749,
    }
    if web:
        # Throw an error if the machine is not connected to the internet
        if ogcore_utils.not_connected():
            err_msg = (
                "SCF DATA ERROR: The local machine is not "
                + "connected to the internet and web=True was "
                + "selected."
            )
            raise RuntimeError(err_msg)

        file_urls = []
        for yr in scf_yrs_list:
            zipfilename = (
                "https://www.federalreserve.gov/econres/"
                + "files/scfp"
                + str(yr)
                + "s.zip"
            )
            file_urls.append(zipfilename)

        file_paths = ogcore_utils.fetch_files_from_web(file_urls)

    elif not web:
        file_paths = []
        if directory is None:
            directory = scf_data_dir
        full_directory = os.path.expanduser(directory)
        filename_list = []
        for yr in scf_yrs_list:
            csv_filename = "scf_wealth_" + str(yr) + ".csv"
            dta_filename = "rscfp" + str(yr) + ".dta"
            if os.path.isfile(os.path.join(full_directory, csv_filename)):
                filename = csv_filename
            else:
                filename = dta_filename
            filename_list.append(filename)

        for name in filename_list:
            file_paths.append(os.path.join(full_directory, name))
        # Check to make sure the necessary files are present in the
        # local directory
        err_msg = (
            "hrs_by_age() ERROR: The file %s was not found in "
            + "the directory %s"
        )
        for path in file_paths:
            if not os.path.isfile(path):
                raise ValueError(err_msg % (path, full_directory))

    # read in raw SCF data to calculate moments
    scf_dict = {}
    columns = ["networth", "wgt"]
    if include_age:
        columns.append("age")
    for filename, year in zip(file_paths, scf_yrs_list):
        if filename.endswith(".csv"):
            csv_columns = ["networth", "networth_infadj", "wgt"]
            if include_age:
                csv_columns.append("age")
            df_yr = pd.read_csv(filename, usecols=csv_columns)
        else:
            df_yr = pd.read_stata(filename, columns=columns)
            # Add inflation adjusted net worth
            cpi = cpi_dict["cpi" + str(year)]
            df_yr["networth_infadj"] = df_yr["networth"] * (100.0 / cpi)
        scf_dict[str(year)] = df_yr

    df_scf = scf_dict[str(scf_yrs_list[0])]
    num_yrs = len(scf_yrs_list)
    if num_yrs >= 2:
        for year in scf_yrs_list[1:]:
            df_scf = pd.concat(
                [df_scf, scf_dict[str(year)]], ignore_index=True
            )

    return df_scf


def compute_wealth_moments(scf, bin_weights):
    """
    This function computes moments (wealth shares, Gini coefficient,
    var[ln(wealth)]) from the distribution of wealth using SCF data.

    Args:
        scf (Pandas DataFrame): pooled cross-sectional data from SCFs
        bin_weights (Numpy Array) = ability weights

    Returns:
        wealth_moments (Numpy Array): array of wealth moments

    """
    # calculate percentile shares (percentiles based on lambdas input)
    scf.sort_values(by="networth_infadj", ascending=True, inplace=True)
    scf["weight_networth"] = scf["wgt"] * scf["networth_infadj"]
    total_weight_wealth = scf.weight_networth.sum()
    cumsum = scf.wgt.cumsum()
    J = bin_weights.shape[0]
    wealth = np.zeros((J,))
    cum_weights = bin_weights.cumsum()
    for i in range(J):
        # Get number of individuals at top of percentile bin
        cutoff = scf.wgt.sum() * cum_weights[i]
        wealth[i] = (
            scf.weight_networth[cumsum < cutoff].sum()
        ) / total_weight_wealth

    wealth_share = np.zeros(J)
    wealth_share[0] = wealth[0]
    wealth_share[1:] = wealth[1:] - wealth[0:-1]

    # compute gini coeff
    scf.sort_values(by="networth_infadj", ascending=True, inplace=True)
    p = (scf.wgt.cumsum() / scf.wgt.sum()).values
    nu = ((scf.wgt * scf.networth_infadj).cumsum()).values
    nu = nu / nu[-1]
    gini_coeff = (nu[1:] * p[:-1]).sum() - (nu[:-1] * p[1:]).sum()

    # compute variance in logs
    df = scf.drop(scf[scf["networth_infadj"] <= 0.0].index)
    df["ln_networth"] = np.log(df["networth_infadj"])
    df.sort_values(by="ln_networth", ascending=True, inplace=True)
    weight_mean = ((df.ln_networth * df.wgt).sum()) / (df.wgt.sum())
    var_ln_wealth = (
        (df.wgt * ((df.ln_networth - weight_mean) ** 2)).sum()
    ) * (1.0 / (df.wgt.sum() - 1))

    wealth_moments = np.append([wealth_share], [gini_coeff, var_ln_wealth])

    return wealth_moments
