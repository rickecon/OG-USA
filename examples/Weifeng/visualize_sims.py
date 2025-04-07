import multiprocessing
from distributed import Client
import os, argparse
import json
import time
import importlib.resources
import copy
from taxcalc import Calculator
import matplotlib.pyplot as plt
from ogusa.calibrate import Calibration
from ogcore.parameters import Specifications
from ogcore import output_tables as ot
from ogcore import output_plots as op
from ogcore.execute import runner
from ogcore.utils import safe_read_pickle

# Use a custom matplotlib style file for plots
style_file_url = (
    "https://raw.githubusercontent.com/PSLmodels/OG-Core/"
    + "master/ogcore/OGcorePlots.mplstyle"
)
plt.style.use(style_file_url)


def main(base_folder, reform_folder):
    # Directories to save data
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))
    save_dir = os.path.join(CUR_DIR, 'Vis_'+base_folder+'_to_'+reform_folder)
    base_dir = os.path.join(CUR_DIR, base_folder, "OUTPUT")
    reform_dir = os.path.join(CUR_DIR, reform_folder, "OUTPUT")

    """
    ------------------------------------------------------------------------
    Save some results of simulations
    ------------------------------------------------------------------------
    """
    base_tpi = safe_read_pickle(os.path.join(base_dir, "TPI", "TPI_vars.pkl"))
    base_params = safe_read_pickle(os.path.join(base_dir, "model_params.pkl"))
    reform_tpi = safe_read_pickle(os.path.join(reform_dir, "TPI", "TPI_vars.pkl"))
    reform_params = safe_read_pickle(os.path.join(reform_dir, "model_params.pkl"))
    
    ans = ot.macro_table(
        base_tpi,
        base_params,
        reform_tpi=reform_tpi,
        reform_params=reform_params,
        var_list=["Y", "C", "K", "L", "r", "w"],
        output_type="pct_diff",
        num_years=10,
        start_year=base_params.start_year,
    )

    # create plots of output
    op.plot_all(
        base_dir,
        reform_dir,
        save_dir,
    )
    # Create CSV file with output
    ot.tp_output_dump_table(
        base_params,
        base_tpi,
        reform_params,
        reform_tpi,
        table_format="csv",
        path=os.path.join(
            save_dir,
            "macro_time_series_output.csv",
        ),
    )

    print("Percentage changes in aggregates:", ans)
    # save percentage change output to csv file
    ans.to_csv(
        os.path.join(
            save_dir, "ogusa_example_output.csv"
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_folder", help="folder for the base sim")
    parser.add_argument("--reform_folder", help="folder for the reform sim")
    args = parser.parse_args()
    main(args.base_folder, args.reform_folder)