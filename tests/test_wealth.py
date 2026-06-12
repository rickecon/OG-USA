"""
Tests of wealth.py module
"""

# import pytest
import pandas as pd
import numpy as np
from ogusa import wealth


def test_get_wealth_data():
    """
    Test of reading wealth data.

    Need SCF data which is too large to check into repo so this will
    be flagged so as to not run on TravisCI.
    """
    df = wealth.get_wealth_data()

    assert isinstance(df, pd.DataFrame)


def test_compute_wealth_moments():
    """
    Test of computation of wealth moments.

    Need SCF data which is too large to check into repo so this will
    be flagged so as to not run on TravisCI.
    """
    expected_moments = np.array(
        [
            -4.32751807e-03,
            1.88493843e-02,
            5.83335020e-02,
            6.06364076e-02,
            1.17479626e-01,
            3.88974639e-01,
            3.60053960e-01,
            8.45596347e-01,
            5.05410152e00,
        ]
    )
    df = wealth.get_wealth_data()
    test_moments = wealth.compute_wealth_moments(
        df, np.array([0.25, 0.25, 0.2, 0.1, 0.1, 0.09, 0.01])
    )

    assert np.allclose(expected_moments, test_moments, rtol=0.001)
