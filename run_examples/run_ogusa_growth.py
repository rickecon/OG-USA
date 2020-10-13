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

    # Grab a reform JSON file already in Tax-Calculator
    # In this example the 'reform' is a change to 2017 law (the
    # baseline policy is tax law in 2018)
    reform_url = ('https://raw.githubusercontent.com/'
                  'PSLmodels/Tax-Calculator/' + taxcalc.__version__ +
                  '/taxcalc/reforms/2017_law.json')
    ref = Calculator.read_json_param_objects(reform_url, None)
    iit_reform = ref['policy']

    # Directories to save data
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))
    base_dir3 = os.path.join(CUR_DIR, 'GROWTH_OUTPUT3')
    base_dir35 = os.path.join(CUR_DIR, 'GROWTH_OUTPUT35')
    base_dir4 = os.path.join(CUR_DIR, 'GROWTH_OUTPUT4')
    base_dir5 = os.path.join(CUR_DIR, 'GROWTH_OUTPUT5')
    base_dir6 = os.path.join(CUR_DIR, 'GROWTH_OUTPUT6')

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

    '''
    ------------------------------------------------------------------------
    Run baseline with 0.03 growth rate
    ------------------------------------------------------------------------
    '''
    og_spec3 = {'frisch': 0.41, 'start_year': START_YEAR, 'cit_rate': [0.21],
                'debt_ratio_ss': 1.0, 'alpha_T': alpha_T.tolist(),
                'alpha_G': alpha_G.tolist(), 'g_y_annual': 0.03}
    tax_func_path = os.path.join(
        CUR_DIR, '..', 'ogusa', 'data', 'tax_functions',
        'TxFuncEst_baseline_CPS.pkl')  # use cached baseline estimates
    kwargs3 = {'output_base': base_dir3, 'baseline_dir': base_dir3,
               'test': False, 'time_path': True, 'baseline': True,
               'og_spec': og_spec3, 'guid': '_base3',
               'run_micro': False, 'tax_func_path': tax_func_path,
               'data': 'cps', 'client': client,
               'num_workers': num_workers}

    start_time3 = time.time()
    runner(**kwargs3)
    elapsed_time3 = time.time()-start_time3
    print('run time = ', elapsed_time3)

    '''
    ------------------------------------------------------------------------
    Run baseline with 0.035 growth rate
    ------------------------------------------------------------------------
    '''
    og_spec35 = {'frisch': 0.41, 'start_year': START_YEAR, 'cit_rate': [0.21],
                 'debt_ratio_ss': 1.0, 'alpha_T': alpha_T.tolist(),
                 'alpha_G': alpha_G.tolist(), 'g_y_annual': 0.035}
    kwargs35 = {'output_base': base_dir35, 'baseline_dir': base_dir35,
                'test': False, 'time_path': True, 'baseline': True,
                'og_spec': og_spec35, 'guid': '_base35',
                'run_micro': False, 'tax_func_path': tax_func_path,
                'data': 'cps', 'client': client,
                'num_workers': num_workers}

    start_time35 = time.time()
    runner(**kwargs35)
    elapsed_time35 = time.time()-start_time35
    print('run time = ', elapsed_time35)

    '''
    ------------------------------------------------------------------------
    Run baseline with 0.04 growth rate
    ------------------------------------------------------------------------
    '''
    og_spec4 = {'frisch': 0.41, 'start_year': START_YEAR, 'cit_rate': [0.21],
                'debt_ratio_ss': 1.0, 'alpha_T': alpha_T.tolist(),
                'alpha_G': alpha_G.tolist(), 'g_y_annual': 0.04}
    kwargs4 = {'output_base': base_dir4, 'baseline_dir': base_dir4,
               'test': False, 'time_path': True, 'baseline': True,
               'og_spec': og_spec4, 'guid': '_base4',
               'run_micro': False, 'tax_func_path': tax_func_path,
               'data': 'cps', 'client': client,
               'num_workers': num_workers}

    start_time4 = time.time()
    runner(**kwargs4)
    elapsed_time4 = time.time()-start_time4
    print('run time = ', elapsed_time4)

    # '''
    # ------------------------------------------------------------------------
    # Run baseline with 0.05 growth rate
    # ------------------------------------------------------------------------
    # '''
    # og_spec5 = {'frisch': 0.41, 'start_year': START_YEAR, 'cit_rate': [0.21],
    #            'debt_ratio_ss': 1.0, 'alpha_T': alpha_T.tolist(),
    #            'alpha_G': alpha_G.tolist(), 'g_y_annual': 0.05}
    # kwargs5 = {'output_base': base_dir5, 'baseline_dir': base_dir5,
    #            'test': False, 'time_path': True, 'baseline': True,
    #            'og_spec': og_spec5, 'guid': '_base5',
    #            'run_micro': False, 'tax_func_path': tax_func_path,
    #            'data': 'cps', 'client': client,
    #            'num_workers': num_workers}

    # start_time5 = time.time()
    # runner(**kwargs5)
    # elapsed_time5 = time.time()-start_time5
    # print('run time = ', elapsed_time5)

    # '''
    # ------------------------------------------------------------------------
    # Run baseline with 0.06 growth rate
    # ------------------------------------------------------------------------
    # '''
    # og_spec6 = {'frisch': 0.41, 'start_year': START_YEAR, 'cit_rate': [0.21],
    #             'debt_ratio_ss': 1.0, 'alpha_T': alpha_T.tolist(),
    #             'alpha_G': alpha_G.tolist(), 'g_y_annual': 0.06}
    # kwargs6 = {'output_base': base_dir6, 'baseline_dir': base_dir6,
    #            'test': False, 'time_path': True, 'baseline': True,
    #            'og_spec': og_spec6, 'guid': '_base6',
    #            'run_micro': False, 'tax_func_path': tax_func_path,
    #            'data': 'cps', 'client': client,
    #            'num_workers': num_workers}

    start_time6 = time.time()
    runner(**kwargs6)
    elapsed_time6 = time.time()-start_time6
    print('run time = ', elapsed_time6)

    # return ans - the percentage changes in macro aggregates and prices
    # due to policy changes from the baseline to the reform
    base_tpi5 = safe_read_pickle(
        os.path.join(base_dir5, 'TPI', 'TPI_vars.pkl'))
    base_params5 = safe_read_pickle(
        os.path.join(base_dir5, 'model_params.pkl'))
    base_tpi6 = safe_read_pickle(
        os.path.join(base_dir6, 'TPI', 'TPI_vars.pkl'))
    base_params6 = safe_read_pickle(
        os.path.join(base_dir6, 'model_params.pkl'))

    # create plots of output

    print("total time was ", (time.time() - run_start_time))
    client.close()


if __name__ == "__main__":
    # execute only if run as a script
    main()
