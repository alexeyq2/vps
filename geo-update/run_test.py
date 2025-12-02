#!/usr/bin/env python3
"""
run_test.py - helper to run a single test from `test_main.py` for VSCode debugging.

This script calls `pytest.main()` in-process so you can set breakpoints in
VSCode and step into tests and the code under test.
"""

import argparse
import sys
import os

try:
    import pytest
except Exception as e:
    print("pytest is required to run tests. Install with: pip install pytest", file=sys.stderr)
    raise


def main():
    # Ensure working directory is the script directory so relative imports work as in tests
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    pytest_args = sys.argv[1:]
    if not pytest_args:
        pytest_args = ['test_geo_update.py']
    
    # How to run a specific test and debug
    if False:
      pytest_args = ['test_geo_update.py::TestUpdateGeo::test_update_geo_with_downloads']
      pytest_args = ['-k test_update_geo_with_downloads']

    # Do not capture stdout so print statements and debugger IO are visible
    pytest_args += ['-s']

    print('Running pytest with args:', pytest_args, file=sys.stderr)
    # Run pytest in the same process to allow debugger to attach to tests
    rc = pytest.main(pytest_args)
    # sys.exit(rc)


if __name__ == '__main__':
    main()
