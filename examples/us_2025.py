import multiprocessing
from distributed import Client
import os
import requests
import json
import time
import importlib.resources
import copy
import cloudpickle
import pickle
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


def main():
    # Define parameters to use for multiprocessing
    num_workers = min(multiprocessing.cpu_count(), 10)
    client = Client(n_workers=num_workers, threads_per_worker=1)
    print("Number of workers = ", num_workers)

    # Directories to save data
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))
    save_dir = os.path.join(CUR_DIR, "US2025")
    base_dir = os.path.join(save_dir, "OUTPUT_BASELINE")
    reform_dir_G = os.path.join(save_dir, "OUTPUT_REFORM_G")
    reform_dir_Gr = os.path.join(save_dir, "OUTPUT_REFORM_Gr")
    reform_dir_regref = os.path.join(save_dir, "OUTPUT_REFORM_RegRef")


    # """
    # ------------------------------------------------------------------------
    # Run baseline policy
    # ------------------------------------------------------------------------
    # """
    # # Read in baseline parameter values from json file
    # # Set up baseline parameterization
    # p = Specifications(
    #     baseline=True,
    #     num_workers=num_workers,
    #     baseline_dir=base_dir,
    #     output_base=base_dir,
    # )
    # # Update parameters for baseline from default json file
    # p.update_specifications(
    #     json.load(
    #         open(
    #             os.path.join(
    #                 CUR_DIR, "us_2025_base_params.json"
    #             )
    #         )
    #     )
    # )

    # # Estimate the tax functions for the baseline

    # # get current policy JSON file
    # base_url = (
    #     "github://PSLmodels:Tax-Calculator@master/taxcalc/"
    #     + "reforms/ext.json"
    # )
    # ref = Calculator.read_json_param_objects(base_url, None)
    # iit_baseline = ref["policy"]
    # c = Calibration(
    #     p,
    #     estimate_tax_functions=True,
    #     iit_baseline=iit_baseline,
    #     client=client,
    # )

    # # close and delete client bc cache is too large
    # client.close()
    # del client

    # d = c.get_dict()

    # # additional parameters to change
    # updated_params = {
    #     "etr_params": d["etr_params"],
    #     "mtrx_params": d["mtrx_params"],
    #     "mtry_params": d["mtry_params"],
    #     "mean_income_data": d["mean_income_data"],
    #     "frac_tax_payroll": d["frac_tax_payroll"],
    # }
    # p.update_specifications(updated_params)

    # # Save baseline parameters as pickle file
    # base_params_path = os.path.join(p.output_base, "model_params.pkl")
    # with open(base_params_path, "wb") as f:
    #     cloudpickle.dump((p), f)

    # # # Import parameters pickle
    # # p = pickle.load(open(os.path.join(base_dir, "model_params.pkl"), "rb"))

    # # Run model
    # client = Client(n_workers=num_workers, threads_per_worker=1)
    # start_time = time.time()
    # runner(p, time_path=True, client=client)
    # print("run time = ", time.time() - start_time)
    # client.close()
    # del client

    # """
    # ---------------------------------------------------------------------------
    # Run reform policy: Cut discretionary government spending by 3.3 percentage
    # points
    # ---------------------------------------------------------------------------
    # """
    # # Read in baseline parameter values from json file
    # # Set up baseline parameterization
    # p_G = Specifications(
    #     baseline=False,
    #     num_workers=num_workers,
    #     baseline_dir=base_dir,
    #     output_base=reform_dir_G,
    # )
    # # Update parameters for baseline from default json file
    # p_G.update_specifications(
    #     json.load(
    #         open(
    #             os.path.join(
    #                 CUR_DIR, "us_2025_refG_params.json"
    #             )
    #         )
    #     )
    # )

    # # Estimate the tax functions for the baseline

    # # get current policy JSON file
    # base_url = (
    #     "github://PSLmodels:Tax-Calculator@master/taxcalc/"
    #     + "reforms/ext.json"
    # )
    # ref = Calculator.read_json_param_objects(base_url, None)
    # iit_baseline = ref["policy"]
    # c_G = Calibration(
    #     p_G,
    #     estimate_tax_functions=True,
    #     iit_baseline=iit_baseline,
    #     client=client,
    # )

    # # close and delete client bc cache is too large
    # client.close()
    # del client

    # d_G = c_G.get_dict()

    # # additional parameters to change
    # updated_params_G = {
    #     "etr_params": d_G["etr_params"],
    #     "mtrx_params": d_G["mtrx_params"],
    #     "mtry_params": d_G["mtry_params"],
    #     "mean_income_data": d_G["mean_income_data"],
    #     "frac_tax_payroll": d_G["frac_tax_payroll"],
    # }
    # p_G.update_specifications(updated_params_G)

    # # Save baseline parameters as pickle file
    # refG_params_path = os.path.join(p_G.output_base, "model_params.pkl")
    # with open(refG_params_path, "wb") as f:
    #     cloudpickle.dump((p_G), f)

    # # Run model
    # client = Client(n_workers=num_workers, threads_per_worker=1)
    # start_time = time.time()
    # runner(p_G, time_path=True, client=client)
    # print("run time = ", time.time() - start_time)
    # client.close()
    # del client

    # """
    # ---------------------------------------------------------------------------
    # Save some results of simulations
    # ---------------------------------------------------------------------------
    # """
    # base_tpi = safe_read_pickle(os.path.join(base_dir, "TPI", "TPI_vars.pkl"))
    # base_params = safe_read_pickle(os.path.join(base_dir, "model_params.pkl"))
    # reform_tpi_G = safe_read_pickle(
    #     os.path.join(reform_dir_G, "TPI", "TPI_vars.pkl")
    # )
    # reform_params_G = safe_read_pickle(
    #     os.path.join(reform_dir_G, "model_params.pkl")
    # )
    # ans_G = ot.macro_table(
    #     base_tpi,
    #     base_params,
    #     reform_tpi=reform_tpi_G,
    #     reform_params=reform_params_G,
    #     var_list=["Y", "C", "K", "L", "r", "w"],
    #     output_type="pct_diff",
    #     num_years=10,
    #     start_year=base_params.start_year,
    # )

    # # create plots of output
    # op.plot_all(
    #     base_dir,
    #     reform_dir_G,
    #     os.path.join(reform_dir_G, "compare_plots_tables")
    # )
    # # Create CSV file with output
    # ot.tp_output_dump_table(
    #     base_params,
    #     base_tpi,
    #     reform_params_G,
    #     reform_tpi_G,
    #     table_format="csv",
    #     path=os.path.join(
    #         reform_dir_G,
    #         "compare_plots_tables",
    #         "macro_time_series_output.csv",
    #     ),
    # )

    # print("Percentage changes in aggregates:", ans_G)
    # # save percentage change output to csv file
    # ans_G.to_csv(
    #     os.path.join(
    #         reform_dir_G, "compare_plots_tables", "aggr_pct_chgs.csv",
    #     )
    # )

    # """
    # ---------------------------------------------------------------------------
    # Run reform policy: Increase TFP by 2%, regulatory reform
    # ---------------------------------------------------------------------------
    # """
    # Read in baseline parameter values from json file
    # Set up baseline parameterization
    p_regref = Specifications(
        baseline=False,
        num_workers=num_workers,
        baseline_dir=base_dir,
        output_base=reform_dir_regref,
    )
    # Update parameters for baseline from default json file
    p_regref.update_specifications(
        json.load(
            open(
                os.path.join(
                    CUR_DIR, "us_2025_refregref_params.json"
                )
            )
        )
    )

    # Estimate the tax functions for the baseline

    # get current policy JSON file
    base_url = (
        "github://PSLmodels:Tax-Calculator@master/taxcalc/"
        + "reforms/ext.json"
    )
    ref = Calculator.read_json_param_objects(base_url, None)
    iit_baseline = ref["policy"]
    c_regref = Calibration(
        p_regref,
        estimate_tax_functions=True,
        iit_baseline=iit_baseline,
        client=client,
    )

    # close and delete client bc cache is too large
    client.close()
    del client

    d_regref = c_regref.get_dict()

    # additional parameters to change
    updated_params_regref = {
        "etr_params": d_regref["etr_params"],
        "mtrx_params": d_regref["mtrx_params"],
        "mtry_params": d_regref["mtry_params"],
        "mean_income_data": d_regref["mean_income_data"],
        "frac_tax_payroll": d_regref["frac_tax_payroll"],
    }
    p_regref.update_specifications(updated_params_regref)

    # Save baseline parameters as pickle file
    refregref_params_path = os.path.join(p_regref.output_base, "model_params.pkl")
    with open(refregref_params_path, "wb") as f:
        cloudpickle.dump((p_regref), f)

    # Run model
    client = Client(n_workers=num_workers, threads_per_worker=1)
    start_time = time.time()
    runner(p_regref, time_path=True, client=client)
    print("run time = ", time.time() - start_time)
    client.close()
    del client

    """
    ---------------------------------------------------------------------------
    Save some results of simulations
    ---------------------------------------------------------------------------
    """
    base_tpi = safe_read_pickle(os.path.join(base_dir, "TPI", "TPI_vars.pkl"))
    base_params = safe_read_pickle(os.path.join(base_dir, "model_params.pkl"))
    reform_tpi_regref = safe_read_pickle(
        os.path.join(reform_dir_regref, "TPI", "TPI_vars.pkl")
    )
    reform_params_regref = safe_read_pickle(
        os.path.join(reform_dir_regref, "model_params.pkl")
    )
    ans_regref = ot.macro_table(
        base_tpi,
        base_params,
        reform_tpi=reform_tpi_regref,
        reform_params=reform_params_regref,
        var_list=["Y", "C", "K", "L", "r", "w"],
        output_type="pct_diff",
        num_years=10,
        start_year=base_params.start_year,
    )

    # create plots of output
    op.plot_all(
        base_dir,
        reform_dir_regref,
        os.path.join(reform_dir_regref, "compare_plots_tables")
    )
    # Create CSV file with output
    ot.tp_output_dump_table(
        base_params,
        base_tpi,
        reform_params_regref,
        reform_tpi_regref,
        table_format="csv",
        path=os.path.join(
            reform_dir_regref,
            "compare_plots_tables",
            "macro_time_series_output.csv",
        ),
    )

    print("Percentage changes in aggregates:", ans_regref)
    # save percentage change output to csv file
    ans_regref.to_csv(
        os.path.join(
            reform_dir_regref, "compare_plots_tables", "aggr_pct_chgs.csv",
        )
    )

    # """
    # ---------------------------------------------------------------------------
    # Run reform policy: Increase labor productivity by 3%, growth
    # ---------------------------------------------------------------------------
    # """
    # # Read in baseline parameter values from json file
    # # Set up baseline parameterization
    # p_gr = Specifications(
    #     baseline=False,
    #     num_workers=num_workers,
    #     baseline_dir=base_dir,
    #     output_base=reform_dir_Gr,
    # )
    # # Update parameters for baseline from default json file
    # p_gr.update_specifications(
    #     json.load(
    #         open(
    #             os.path.join(
    #                 CUR_DIR, "us_2025_refgr_params.json"
    #             )
    #         )
    #     )
    # )

    # # Estimate the tax functions for the baseline

    # # get current policy JSON file
    # base_url = (
    #     "github://PSLmodels:Tax-Calculator@master/taxcalc/"
    #     + "reforms/ext.json"
    # )
    # ref = Calculator.read_json_param_objects(base_url, None)
    # iit_baseline = ref["policy"]
    # c_gr = Calibration(
    #     p_gr,
    #     estimate_tax_functions=True,
    #     iit_baseline=iit_baseline,
    #     client=client,
    # )

    # # close and delete client bc cache is too large
    # client.close()
    # del client

    # d_gr = c_gr.get_dict()

    # # additional parameters to change
    # updated_params_gr = {
    #     "etr_params": d_gr["etr_params"],
    #     "mtrx_params": d_gr["mtrx_params"],
    #     "mtry_params": d_gr["mtry_params"],
    #     "mean_income_data": d_gr["mean_income_data"],
    #     "frac_tax_payroll": d_gr["frac_tax_payroll"],
    # }
    # p_gr.update_specifications(updated_params_gr)

    # # Save baseline parameters as pickle file
    # refgr_params_path = os.path.join(p_gr.output_base, "model_params.pkl")
    # with open(refgr_params_path, "wb") as f:
    #     cloudpickle.dump((p_gr), f)

    # # Run model
    # client = Client(n_workers=num_workers, threads_per_worker=1)
    # start_time = time.time()
    # runner(p_gr, time_path=True, client=client)
    # print("run time = ", time.time() - start_time)
    # client.close()
    # del client

    # """
    # ---------------------------------------------------------------------------
    # Save some results of simulations
    # ---------------------------------------------------------------------------
    # """
    # base_tpi = safe_read_pickle(os.path.join(base_dir, "TPI", "TPI_vars.pkl"))
    # base_params = safe_read_pickle(os.path.join(base_dir, "model_params.pkl"))
    # reform_tpi_gr = safe_read_pickle(
    #     os.path.join(reform_dir_Gr, "TPI", "TPI_vars.pkl")
    # )
    # reform_params_gr = safe_read_pickle(
    #     os.path.join(reform_dir_Gr, "model_params.pkl")
    # )
    # ans_gr = ot.macro_table(
    #     base_tpi,
    #     base_params,
    #     reform_tpi=reform_tpi_gr,
    #     reform_params=reform_params_gr,
    #     var_list=["Y", "C", "K", "L", "r", "w"],
    #     output_type="pct_diff",
    #     num_years=10,
    #     start_year=base_params.start_year,
    # )

    # # create plots of output
    # op.plot_all(
    #     base_dir,
    #     reform_dir_Gr,
    #     os.path.join(reform_dir_Gr, "compare_plots_tables")
    # )
    # # Create CSV file with output
    # ot.tp_output_dump_table(
    #     base_params,
    #     base_tpi,
    #     reform_params_gr,
    #     reform_tpi_gr,
    #     table_format="csv",
    #     path=os.path.join(
    #         reform_dir_Gr,
    #         "compare_plots_tables",
    #         "macro_time_series_output.csv",
    #     ),
    # )

    # print("Percentage changes in aggregates:", ans_gr)
    # # save percentage change output to csv file
    # ans_gr.to_csv(
    #     os.path.join(
    #         reform_dir_Gr, "compare_plots_tables", "aggr_pct_chgs.csv",
    #     )
    # )


if __name__ == "__main__":
    # execute only if run as a script
    main()
