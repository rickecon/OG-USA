import multiprocessing
from distributed import Client
import os
import json
import time
from taxcalc import Calculator
from ogusa.calibrate import Calibration
from ogcore.parameters import Specifications
from ogcore import output_tables as ot
from ogcore import output_plots as op
from ogcore.execute import runner
from ogcore.utils import safe_read_pickle, mkdirs


def main():
    # Define parameters to use for multiprocessing
    client = Client()
    num_workers = min(multiprocessing.cpu_count(), 7)
    print("Number of workers = ", num_workers)

    # Directories to save data
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))
    base_dir = os.path.join(CUR_DIR, "OG-USA-DebtDef", "OUTPUT_BASELINE")
    reform_dir = os.path.join(CUR_DIR, "OG-USA-DebtDef", "OUTPUT_REFORM_T340")
    reform_dir_images = os.path.join(reform_dir, "images")
    mkdirs(reform_dir_images)

    """
    ------------------------------------------------------------------------
    Run reform policy
    ------------------------------------------------------------------------
    """
    # Reform dictionary
    pct_incr = 0.340
    reform_dict = \
        {
            # Personal income (regular/non-AMT/non-pass-through) tax rates
            "II_rt1": {"2021": (1 + pct_incr) * 0.10,
                       "2026": (1 + pct_incr) * 0.10},
            "II_rt2": {"2021": (1 + pct_incr) * 0.12,
                       "2026": (1 + pct_incr) * 0.15},
            "II_rt3": {"2021": (1 + pct_incr) * 0.22,
                       "2026": (1 + pct_incr) * 0.25},
            "II_rt4": {"2021": (1 + pct_incr) * 0.24,
                       "2026": (1 + pct_incr) * 0.28},
            "II_rt5": {"2021": (1 + pct_incr) * 0.32,
                       "2026": (1 + pct_incr) * 0.33},
            "II_rt6": {"2021": (1 + pct_incr) * 0.35,
                       "2026": (1 + pct_incr) * 0.35},
            "II_rt7": {"2021": (1 + pct_incr) * 0.37,
                       "2026": (1 + pct_incr) * 0.396},
            # Pass-through income tax rates
            "PT_rt1": {"2021": (1 + pct_incr) * 0.10,
                       "2026": (1 + pct_incr) * 0.10},
            "PT_rt2": {"2021": (1 + pct_incr) * 0.12,
                       "2026": (1 + pct_incr) * 0.15},
            "PT_rt3": {"2021": (1 + pct_incr) * 0.22,
                       "2026": (1 + pct_incr) * 0.25},
            "PT_rt4": {"2021": (1 + pct_incr) * 0.24,
                       "2026": (1 + pct_incr) * 0.28},
            "PT_rt5": {"2021": (1 + pct_incr) * 0.32,
                       "2026": (1 + pct_incr) * 0.33},
            "PT_rt6": {"2021": (1 + pct_incr) * 0.35,
                       "2026": (1 + pct_incr) * 0.35},
            "PT_rt7": {"2021": (1 + pct_incr) * 0.37,
                       "2026": (1 + pct_incr) * 0.396},
            # # Payroll tax rate (Social Security)
            # "FICA_ss_trt": {"2021": (1 + pct_incr) * 0.124},
            # "FICA_mc_trt": {"2021": (1 + pct_incr) * 0.029},
        }
    ref = Calculator.read_json_param_objects(reform_dict, None)
    iit_reform = ref["policy"]

    # create new Specifications object for reform simulation
    p2 = Specifications(
        baseline=False,
        num_workers=num_workers,
        baseline_dir=base_dir,
        output_base=reform_dir,
    )
    # Update parameters for baseline from default json file
    p2.update_specifications(
        json.load(
            open(
                os.path.join(
                    CUR_DIR, "..", "ogusa", "ogusa_default_parameters.json"
                )
            )
        )
    )
    # Use calibration class to estimate reform tax functions from
    # Tax-Calculator, specifing reform for Tax-Calculator in pit_reform
    tax_func_path = os.path.join(reform_dir, 'TxFuncEst_policy.pkl')
    c2 = Calibration(
        p2, iit_reform=iit_reform, estimate_tax_functions=False,
        tax_func_path = tax_func_path, client=client
    )
    # additional parameters to change
    updated_params = {
        "tG1": 29,
        "initial_debt_ratio": 1.0,
        "alpha_T": [0.0725],
        "debt_ratio_ss": 1.35,
        "cit_rate": [(1 + pct_incr) * 0.21],
        "etr_params": c2.tax_function_params["etr_params"],
        "mtrx_params": c2.tax_function_params["mtrx_params"],
        "mtry_params": c2.tax_function_params["mtry_params"],
        "mean_income_data": c2.tax_function_params["mean_income_data"],
        "frac_tax_payroll": c2.tax_function_params["frac_tax_payroll"],
    }
    p2.update_specifications(updated_params)
    # Run model
    start_time = time.time()
    runner(p2, time_path=True, client=client)
    print("run time = ", time.time() - start_time)
    client.close()

    """
    ------------------------------------------------------------------------
    Save some results of simulations
    ------------------------------------------------------------------------
    """
    base_tpi = safe_read_pickle(os.path.join(base_dir, "TPI", "TPI_vars.pkl"))
    base_params = safe_read_pickle(os.path.join(base_dir, "model_params.pkl"))
    reform_tpi = safe_read_pickle(
        os.path.join(reform_dir, "TPI", "TPI_vars.pkl")
    )
    reform_params = safe_read_pickle(
        os.path.join(reform_dir, "model_params.pkl")
    )
    ans = ot.macro_table(
        base_tpi,
        base_params,
        reform_tpi=reform_tpi,
        reform_params=reform_params,
        var_list=["Y", "C", "K", "L", "r", "w"],
        output_type="pct_diff",
        num_years=10,
        start_year=base_params.start_year
    )

    # create plots of output
    op.plot_all(base_dir, reform_dir, reform_dir_images)

    print("Percentage changes in aggregates:", ans)
    # save percentage change output to csv file
    ans.to_csv(os.path.join(reform_dir, "ogusa_macrotable_output.csv"))


if __name__ == "__main__":
    # execute only if run as a script
    main()
