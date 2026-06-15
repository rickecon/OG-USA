import os
import pytest
import matplotlib
matplotlib.use("Agg")


def pytest_collection_modifyitems(config, items):
    if not os.environ.get("FRED_API_KEY"):
        skip_fred = pytest.mark.skip(reason="FRED_API_KEY not set")
        for item in items:
            if "needs_fred" in item.keywords:
                item.add_marker(skip_fred)
