"""
Download the most recent vintages of the Federal Reserve Survey of Consumer
Finances (SCF) summary extract and compute:

1. Total U.S. household wealth defined as domestic holdings of domestic
   private assets (K_d) plus domestic holdings of domestic government debt
   (D_d).
2. The share of that wealth held by households by 10-year age bin of the
   head of household (21-30, ..., 91-100) and lifetime income group j
   (OG-Core ``lambdas``): an (8, 7) matrix, a (7,) vector by lifetime income
   group, and an (8,) vector by age bin.

Notes on the mapping from SCF variables to model concepts:

- The starting point is SCF household net worth (NETWORTH). Household
  liabilities are netted out because they are claims held by other domestic
  agents.
- D_d is direct holdings of government debt: U.S. savings bonds (SAVBND),
  federal government and agency bonds (GOVTBND), state and local tax-exempt
  bonds (NOTXBND), government bond mutual funds (GBMUTF), and tax-free bond
  mutual funds (TFBMUTF). Government debt held indirectly through retirement
  accounts, annuities, trusts, and life insurance cannot be identified in the
  SCF and is counted in K_d.
- The SCF does not identify whether equities or corporate bonds are issued
  by foreign entities. Set FOREIGN_EQUITY_SHARE and FOREIGN_BOND_SHARE (e.g.,
  from the Financial Accounts of the U.S., Z.1, tables L.224 and L.223 on
  U.S. residents' holdings of foreign corporate equities and debt securities)
  to remove foreign holdings. They default to zero.
- The public SCF top-codes age at 95, so the 91-100 age bin includes all
  households with head age 91 and older.
- Lifetime income is not observed in a cross section. Households are
  assigned to lifetime income groups by their weighted percentile of SCF
  "normal" income (NORMINC) within 5-year age bins, so each age has the
  population distribution given by LAMBDAS.
- Each household appears five times (implicates) and WGT = X42001 / 5, so
  weighted sums over all rows are population totals.
"""

import datetime
import io
import os
import urllib.error
import urllib.request
import zipfile
import numpy as np
import pandas as pd
import ogusa.utils as utilsusa

HEADERS = {"User-Agent": "Mozilla/5.0"}
FIRST_SCF_YEAR = 1989  # SCF is triennial: 1989, 1992, ..., 2019, 2022
NUM_VINTAGES = 2
MIN_AGE, MAX_AGE = 21, 100
AGE_BIN_WIDTH = 5  # age bins within which lifetime income is ranked
DIST_AGE_BIN_WIDTH = 10  # age bins for the output wealth distributions
# OG-Core default lifetime income group population shares
LAMBDAS = np.array([0.25, 0.25, 0.2, 0.1, 0.1, 0.09, 0.01])
FOREIGN_EQUITY_SHARE = 0.0  # share of SCF equity holdings issued abroad
FOREIGN_BOND_SHARE = 0.0  # share of SCF non-gov't bond holdings issued abroad
EXCLUDE_DURABLES = False  # if True, drop vehicles and other nonfinancial
CUR_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(CUR_DIR, "data", "SCF")


def find_recent_vintages(num_vintages=NUM_VINTAGES):
    """
    Return the years of the most recent SCF vintages available on the
    Federal Reserve website, newest first.
    """
    scf_url = (
        "https://www.federalreserve.gov/econres/files/scfp{year}s.zip"
    )
    this_year = datetime.date.today().year
    latest = this_year - (this_year - FIRST_SCF_YEAR) % 3
    years = []
    for year in range(latest, FIRST_SCF_YEAR - 1, -3):
        if utilsusa._url_exists(scf_url.format(year=year)):
            years.append(year)
        if len(years) == num_vintages:
            break
    return years


def load_scf(year, web=False, data_dir=DATA_DIR):
    """
    Download (or read the cached copy of) the SCF summary extract for a
    given survey year and return it as a DataFrame.
    """
    zip_path = os.path.join(data_dir, f"scfp{year}s.zip")
    if web:
        scf_headers = {"User-Agent": "Mozilla/5.0"}
        scf_url = (
            "https://www.federalreserve.gov/econres/files/scfp{year}s.zip"
        )
        os.makedirs(data_dir, exist_ok=True)
        if not os.path.exists(zip_path):
            print(f"Downloading SCF {year} summary extract...")
            request = urllib.request.Request(
                scf_url.format(year=year), headers=scf_headers
            )
        with urllib.request.urlopen(request, timeout=300) as response:
            with open(zip_path, "wb") as f:
                f.write(response.read())
    with zipfile.ZipFile(zip_path) as zf:
        dta_name = [n for n in zf.namelist() if n.endswith(".dta")][0]
        df = pd.read_stata(io.BytesIO(zf.read(dta_name)))
    df.columns = df.columns.str.lower()
    return df


def compute_wealth(df_scf, scf_year):
    """
    Add columns for domestic government debt holdings (D_d), domestic
    private asset holdings (K_d), and their sum (wealth) to the DataFrame. Put
    dollar amounts in terms of the most recent CPI base year terms.
    """
    # Set CPI value for the scf_year (cpi_scf_year) as the monthly CPI index
    # value in July of that year.
    df_cpi = utilsusa.get_cpi_monthly_data(start_year=scf_year)
    # Set cpi_scf_year to be the July CPI value for the scf_year in df_cpi
    cpi_scf_year = df_cpi
    #
    gov_debt = (
        df_scf["savbnd"] + df_scf["govtbnd"] + df_scf["notxbnd"] +
        df_scf["gbmutf"] + df_scf["tfbmutf"]
    )
    # EQUITY counts half of combination funds as equity, so the other half
    # is counted as bonds here
    foreign = FOREIGN_EQUITY_SHARE * df["equity"] + FOREIGN_BOND_SHARE * (
        df["obnd"] + df["obmutf"] + 0.5 * df["comutf"]
    )
    wealth = df["networth"] - foreign
    if EXCLUDE_DURABLES:
        wealth = wealth - df["vehic"] - df["othnfin"]
    df["D_d"] = gov_debt
    df["K_d"] = wealth - gov_debt
    df["wealth"] = wealth
    return df


def assign_lifetime_income_group(df, lambdas=LAMBDAS):
    """
    Assign each household to lifetime income group j = 0, ..., J-1 by its
    weighted percentile of normal income within its age bin.
    """
    df["age_bin"] = (df["age"] - MIN_AGE) // AGE_BIN_WIDTH
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


def wealth_distributions(df, lambdas=LAMBDAS):
    """
    Return the share of total wealth held by households by 10-year age bin
    of the head of household and lifetime income group j as an
    (age bins x J) DataFrame, a (J,) Series by lifetime income group, and
    an (age bins,) Series by age bin.
    """
    bin_starts = range(MIN_AGE, MAX_AGE + 1, DIST_AGE_BIN_WIDTH)
    age_labels = [f"{a}-{a + DIST_AGE_BIN_WIDTH - 1}" for a in bin_starts]
    age_bin = (df["age"] - MIN_AGE) // DIST_AGE_BIN_WIDTH
    df = df.assign(w_wealth=df["wgt"] * df["wealth"], dist_age_bin=age_bin)
    cell_wealth = df.groupby(["dist_age_bin", "j"])["w_wealth"].sum().unstack()
    cell_wealth = cell_wealth.reindex(
        index=range(len(age_labels)), columns=range(len(lambdas))
    ).fillna(0.0)
    dist_2d = cell_wealth / df["w_wealth"].sum()
    dist_2d.index = pd.Index(age_labels, name="age")
    dist_2d.columns = pd.Index(
        [f"j={j}" for j in dist_2d.columns], name="lifetime income group"
    )
    return dist_2d, dist_2d.sum(axis=0), dist_2d.sum(axis=1)


def analyze_vintage(year):
    df = load_scf(year)
    df = compute_wealth(df)
    total_all_ages = {
        var: (df["wgt"] * df[var]).sum() / 1e12
        for var in ["networth", "wealth", "K_d", "D_d"]
    }
    df = df[df["age"] >= MIN_AGE].copy()
    df = assign_lifetime_income_group(df)
    summary = pd.Series(
        {
            "households (millions)": df["wgt"].sum() / 1e6,
            "net worth, all ages ($tn)": total_all_ages["networth"],
            "K_d + D_d, all ages ($tn)": total_all_ages["wealth"],
            f"K_d + D_d, ages {MIN_AGE}+ ($tn)": (
                df["wgt"] * df["wealth"]
            ).sum()
            / 1e12,
            f"K_d, ages {MIN_AGE}+ ($tn)": (df["wgt"] * df["K_d"]).sum()
            / 1e12,
            f"D_d, ages {MIN_AGE}+ ($tn)": (df["wgt"] * df["D_d"]).sum()
            / 1e12,
        },
        name=year,
    )
    return summary, wealth_distributions(df)


def main():
    years = find_recent_vintages()
    print("SCF vintages:", years)
    summaries = []
    for year in years:
        summary, (dist_2d, dist_j, dist_age) = analyze_vintage(year)
        summaries.append(summary)
        dist_2d.to_csv(os.path.join(DATA_DIR, f"wealth_dist_age_j_{year}.csv"))
        dist_j.rename("wealth share").to_csv(
            os.path.join(DATA_DIR, f"wealth_dist_j_{year}.csv")
        )
        dist_age.rename("wealth share").to_csv(
            os.path.join(DATA_DIR, f"wealth_dist_age_{year}.csv")
        )
        print(f"\n===== SCF {year} (nominal {year} dollars) =====")
        print(summary.round(2).to_string())
        print(
            f"\nShare of wealth by age bin and lifetime income group "
            f"{dist_2d.shape}:"
        )
        print(dist_2d.round(4).to_string())
        print(f"\nShare of wealth by lifetime income group {dist_j.shape}:")
        print(dist_j.round(4).to_string())
        print(f"\nShare of wealth by age bin {dist_age.shape}:")
        print(dist_age.round(4).to_string())
    pd.concat(summaries, axis=1).to_csv(
        os.path.join(DATA_DIR, "wealth_totals.csv")
    )
    print(f"\nSaved output to {DATA_DIR}")


if __name__ == "__main__":
    main()
