#!/usr/bin/env python3
"""
run_test.py - helper to run a single test from `test_main.py` for VSCode debugging.

Usage examples:
  python run_test.py                     # run all tests in test_main.py
  python run_test.py --test TestClass::test_method
  python run_test.py --test test_function
  python run_test.py --pattern "name_part"
  python run_test.py --file other_test.py --test SomeTest::test_name

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
    parser = argparse.ArgumentParser(description="Run a single pytest test from test_main.py (helper for debugging)")
    parser.add_argument('--file', '-f', default='test_geo_update.py', help='Test file to run (default: test_geo_update.py)')
    parser.add_argument('--test', '-t', help='Test nodeid or name. Examples: "TestClass::test_method" or "test_function"')
    parser.add_argument('--pattern', '-k', help='pytest -k expression to filter tests (mutually exclusive with --test)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Pass -vv to pytest')
    args = parser.parse_args()

    # Ensure working directory is the script directory so relative imports work as in tests
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    pytest_args = []

    if False:
      if args.test:
          # If the user provided a full nodeid (contains :: or ends with .py), use it directly
          if '::' in args.test or args.test.endswith('.py') or os.path.isabs(args.test):
              pytest_args = [args.test]
          else:
              pytest_args = [f"{args.file}::{args.test}"]
      elif args.pattern:
          pytest_args = [args.file, '-k', args.pattern]
      else:
          pytest_args = [args.file]
      if args.verbose:
          pytest_args.insert(0, '-vv')
    else:
      pytest_args = ['test_geo_update.py::TestUpdateGeo::test_update_geo_with_downloads']

    # Do not capture stdout so print statements and debugger IO are visible
    pytest_args += ['-s']

    print('Running pytest with args:', pytest_args, file=sys.stderr)
    # Run pytest in the same process to allow debugger to attach to tests
    rc = pytest.main(pytest_args)
    
    # Exit with pytest return code
    # sys.exit(rc)


if __name__ == '__main__':
    main()
