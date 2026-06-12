# OG-USA

| | |
| --- | --- |
| Org | [![PSL cataloged](https://img.shields.io/badge/PSL-cataloged-a0a0a0.svg)](https://www.PSLmodels.org) [![OS License: CC0-1.0](https://img.shields.io/badge/OS%20License-CC0%201.0-yellow)](https://github.com/PSLmodels/OG-USA/blob/master/LICENSE) [![Jupyter Book Badge](https://raw.githubusercontent.com/jupyter-book/jupyter-book/next/docs/media/images/badge.svg)](https://github.com/PSLmodels/OG-USA/) |
| Package | [![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3129/) [![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-31312/) [![PyPI Latest Release](https://img.shields.io/pypi/v/ogusa.svg)](https://pypi.org/project/ogusa/) [![PyPI Downloads](https://img.shields.io/pypi/dm/ogusa.svg?label=PyPI%20downloads)](https://pypi.org/project/ogusa/) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) |
| Testing | ![example event parameter](https://github.com/PSLmodels/OG-USA/actions/workflows/build_and_test.yml/badge.svg?branch=master) ![example event parameter](https://github.com/PSLmodels/OG-USA/actions/workflows/deploy_docs.yml/badge.svg?branch=master) ![example event parameter](https://github.com/PSLmodels/OG-USA/actions/workflows/check_ruff.yml/badge.svg?branch=master) [![Codecov](https://codecov.io/gh/PSLmodels/OG-USA/branch/master/graph/badge.svg)](https://codecov.io/gh/PSLmodels/OG-USA) |

OG-USA is an overlapping-generations (OG) model that allows for dynamic general equilibrium analysis of fiscal policy for the United States. OG-USA is built on the [OG-Core](https://github.com/PSLmodels/OG-Core) framework. The model output includes changes in macroeconomic aggregates (GDP, investment, consumption), wages, interest rates, and the stream of tax revenues over time. Regularly updated documentation of the model theory--its output, and solution method--and the Python API is available at [https://pslmodels.github.io/OG-Core](https://pslmodels.github.io/OG-Core) and documentation of the specific United States calibration of the model is available at [https://pslmodels.github.io/OG-USA](https://pslmodels.github.io/OG-USA).


## Disclaimer

The model is constantly under development, and model components could change significantly. The package will have released versions, which will be checked against existing code prior to release. Stay tuned for an upcoming release!



## Using/contributing to OG-USA

There are two primary methods for installing and running OG-USA on your computer locally. The first and simplest method is to download the most recent `ogusa` Python package from the Python Package Index ([PyPI.org](https://pypi.org/project/ogusa/)). The second option is to fork and clone the most recent version of OG-USA from its GitHub repository and install the `ogusa` package with its development dependencies using `uv`. Both methods are detailed below.

### Installing and Running OG-USA from PyPI

* On macOS, first install Xcode Command Line Tools (in Terminal: `xcode-select --install`).
* Open your terminal and install the [`ogusa`](https://pypi.org/project/ogusa/) package from the Python Package Index by typing `pip install ogusa`.
* Navigate to a folder `./YourFolderName/` where you want to save scripts to run OG-USA and output from the simulations in those scripts.
* Copy the python script [`run_og_usa.py`](https://github.com/PSLmodels/OG-USA/blob/master/examples/run_og_usa.py) from the OG-USA GitHub repository into your folder as `./YourFolderName/run_og_usa.py`.
* Run the model with an example reform from terminal/command prompt by typing `python run_og_usa.py`.


### Installing and Running OG-USA from the GitHub repository

* On macOS, first install Xcode Command Line Tools (in Terminal: `xcode-select --install`).
* Install [`uv`](https://docs.astral.sh/uv/) by following the [installation instructions](https://docs.astral.sh/uv/getting-started/installation/) for your platform (or simply run `pip install uv`).
* Fork this repository and clone your fork to a directory on your computer.
* From the terminal, navigate to the cloned directory and run `uv sync --extra dev` to create a local `.venv` and install OG-USA with its development dependencies. `uv` will also download a compatible Python interpreter if you don't already have one.
* For docs/Jupyter Book work, also run `uv sync --extra dev --extra docs`.


### Run an example of the model
* Install [`uv`](https://docs.astral.sh/uv/) by following the
  [installation instructions](https://docs.astral.sh/uv/getting-started/installation/)
  for your platform, or by running `pip install uv`.
* Clone this repository to a directory on your computer
* From the terminal, navigate to the directory to which you cloned this
  repository and run `uv sync --extra dev`.
* Navigate to `./examples`
* Run the model with an example reform from terminal/command prompt by
  typing `uv run python run_ogusa.py`
* You can adjust the `./examples/run_ogusa.py` by modifying model parameters specified in the dictionary passed to the `p.update_specifications()` calls.
* Model outputs will be saved in the following files:
    * `./examples/Example/`: This folder will contain all of the output from the `run_ogusa.py` run script.
        * `./examples/Example/example_plots_tables`: This folder will contain a number of plots and tables generated from the `run_ogusa.py` run script to help you visualize the output.
        * `./examples/Example/example_output.csv`: This is a summary of the percentage changes in macro variables over the first ten years and in the steady-state.
    * `./examples/Example/OUTPUT_BASELINE/`: This folder contains all of the inputs to and outputs from the baseline equilibrium computation from `run_ogusa.py`
        * `./examples/Example/OUTPUT_BASELINE/model_params.pkl`: Pickle binary file of ParamTools object of model parameters used in the baseline run
        * `./examples/Example/OUTPUT_BASELINE/SS/SS_vars.pkl`: Pickle binary file of Python dictionary of outputs from the model steady state solution under the baseline policy. See [`ogcore.SS.py`](https://github.com/PSLmodels/OG-Core/blob/master/ogcore/SS.py) for what is in the dictionary object in this pickle file
        * `./examples/Example/OUTPUT_BASELINE/TPI/TPI_vars.pkl`: Pickle binary file of Python dictionary of outputs from the model timepath solution under the baseline policy. See [`ogcore.TPI.py`](https://github.com/PSLmodels/OG-Core/blob/master/ogcore/TPI.py) for what is in the dictionary object in this pickle file
    * An analogous set of files in the `./examples/OUTPUT_REFORM` directory, which represent objects from the simulation of the reform policy.

Note that, depending on your machine, a full model run (solving for the full time path equilibrium for the baseline and reform policies) can take more than two hours of compute time.

If you run into errors running the example script, please open a new issue in the OG-USA repo with a description of the issue and any relevant tracebacks you receive.

Once the package is installed, one can adjust parameters in the OG-Core `Specifications` object using the `Calibration` class as follows:

```
from ogcore.parameters import Specifications
from ogusa.calibrate import Calibration
p = Specifications()
c = Calibration(p)
updated_params = c.get_dict()
p.update_specifications({'initial_debt_ratio': updated_params['initial_debt_ratio']})
```


## Core Maintainers

The core maintainers of the OG-Core repository are:

* [Jason DeBacker](https://www.jasondebacker.com/) (GitHub handle: [jdebacker](https://github.com/jdebacker)), Associate Professor, Department of Economics, Darla Moore School of Business, University of South Carolina; President, PSL Foundation; Vice President of Research and Co-founder, Open Research Group, Inc.
* [Richard W. Evans](https://sites.google.com/site/rickecon/) (GitHub handle: [rickecon](https://github.com/rickecon)), Senior Economist, Abundance Institute; President, Open Research Group, Inc.; Director, Open Source Economics Laboratory.

## Citing OG-USA

OG-USA (Version #.#.#)[Source code], https://github.com/PSLmodels/OG-USA.
