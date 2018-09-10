# Continuous Integration (CI)

We use [Travis CI](https://travis-ci.org/brunorijsman/rift-python) and 
[codecov](https://codecov.io/gh/brunorijsman/rift-python) for Continuous Integration (CI).

For every commit Travis CI runs pylint on all production code and test code. The pylint score must
be a perfect 10.0. The build fails if there is even a single pylint warning (except for those
explicitly allowed by pylintrc or by pylint comments in the code).

For every commit Travis CI also runs the complete test suite, both the unit tests and the system
tests. If any test fails, the build fails.

Travis CI runs pytest with the --cov option to measure code coverage. The results are automatically
uploaded to codecov which provides graphical code coverage reports.

The [README.md](../README.md) file contains badges to report the Travis CI build result and to 
report the codecov coverage percentage.

Before you commit code, you must run the tools/pre-commit-checks bash script to make sure that
pylint is perfect and all unit tests pass.
