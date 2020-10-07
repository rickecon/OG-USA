'''
Example script for setting policy and running OG-USA.
'''

# import modules
import multiprocessing
from distributed import Client
import time
import numpy as np
import os
import taxcalc
from taxcalc import Calculator
from ogusa import wealth
from ogusa import output_tables as ot
from ogusa import output_plots as op
from ogusa.execute import runner
from ogusa.constants import REFORM_DIR, BASELINE_DIR
from ogusa.utils import safe_read_pickle


def main():
    # Define parameters to use for multiprocessing
    client = Client()
    num_workers = min(multiprocessing.cpu_count(), 7)
    print('Number of workers = ', num_workers)
    run_start_time = time.time()

    # Directories to save data
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))
    base_dir = os.path.join(CUR_DIR, BASELINE_DIR)
    reform_dir = os.path.join(CUR_DIR, REFORM_DIR)

    # Set some OG model parameters
    # See default_parameters.json for more description of these parameters
    alpha_T = np.zeros(50)  # Adjusting the path of transfer spending
    alpha_T[0:2] = 0.09
    alpha_T[2:10] = 0.09 + 0.01
    alpha_T[10:40] = 0.09 - 0.01
    alpha_T[40:] = 0.09
    alpha_G = np.zeros(7)  # Adjusting the path of non-transfer spending
    alpha_G[0:3] = 0.05 - 0.01
    alpha_G[3:6] = 0.05 - 0.005
    alpha_G[6:] = 0.05
    # Set start year for baseline and reform.
    START_YEAR = 2021
    # Also adjust the Frisch elasticity, the start year, the
    # effective corporate income tax rate, and the SS debt-to-GDP ratio
    og_spec1 = {'frisch': 0.41, 'start_year': START_YEAR, 'cit_rate': [0.21],
                'debt_ratio_ss': 1.0, 'alpha_T': alpha_T.tolist(),
                'alpha_G': alpha_G.tolist()}

    '''
    ------------------------------------------------------------------------
    Run original baseline policy first
    ------------------------------------------------------------------------
    '''
    tax_func_path = os.path.join(
        CUR_DIR, '..', 'ogusa', 'data', 'tax_functions',
        'TxFuncEst_baseline_CPS.pkl')  # use cached baseline estimates
    kwargs1 = {'output_base': base_dir, 'baseline_dir': base_dir,
               'test': False, 'time_path': True, 'baseline': True,
               'og_spec': og_spec1, 'guid': '_base1',
               'run_micro': False, 'tax_func_path': tax_func_path,
               'data': 'cps', 'client': client,
               'num_workers': num_workers}

    start_time1 = time.time()
    runner(**kwargs1)
    print('run time = ', time.time()-start_time1)

    '''
    ------------------------------------------------------------------------
    Run new baseline policy with adjusted chi_b vector
    ------------------------------------------------------------------------
    '''
    chi_b = np.array([40.0, 45.0, 55.0, 75.0, 105.0, 150.0, 200.0])
    og_spec2 = {'frisch': 0.41, 'start_year': START_YEAR, 'cit_rate': [0.21],
                'debt_ratio_ss': 1.0, 'alpha_T': alpha_T.tolist(),
                'chi_b': chi_b, 'alpha_G': alpha_G.tolist()}

    kwargs2 = {'output_base': reform_dir, 'baseline_dir': reform_dir,
               'test': False, 'time_path': True, 'baseline': True,
               'og_spec': og_spec2, 'guid': '_base2',
               'run_micro': False, 'tax_func_path': tax_func_path,
               'data': 'cps', 'client': client,
               'num_workers': num_workers}

    start_time2 = time.time()
    runner(**kwargs2)
    print('run time = ', time.time()-start_time2)

    print("total time was ", (time.time() - run_start_time))
    client.close()

    # return ans - the percentage changes in macro aggregates and prices
    # due to policy changes from the baseline to the reform
    base_params1 = safe_read_pickle(
        os.path.join(base_dir, 'model_params.pkl'))
    base_ss1 = safe_read_pickle(
        os.path.join(base_dir, 'SS', 'SS_vars.pkl'))
    base_tpi1 = safe_read_pickle(
        os.path.join(base_dir, 'TPI', 'TPI_vars.pkl'))
    base_params2 = safe_read_pickle(
        os.path.join(reform_dir, 'model_params.pkl'))
    base_ss2 = safe_read_pickle(
        os.path.join(reform_dir, 'SS', 'SS_vars.pkl'))
    base_tpi2 = safe_read_pickle(
        os.path.join(reform_dir, 'TPI', 'TPI_vars.pkl'))

    wealth.compute_wealth_moments()


    print('Baseline 1 chi_b is:', base_params1.chi_b)
    print('Baseline 2 chi_b is:', base_params2.chi_b)

    # Create transition table
    ans = ot.macro_table(
        base_tpi1, base_params1, reform_tpi=base_tpi2,
        reform_params=base_params2,
        var_list=['Y', 'C', 'K', 'L', 'r', 'w'], output_type='pct_diff',
        num_years=10, start_year=og_spec1['start_year'])

    # Create figures
    op.plot_all(base_dir, reform_dir,
                os.path.join(CUR_DIR, 'run_example_plots'))


if __name__ == "__main__":
    # execute only if run as a script
    main()
