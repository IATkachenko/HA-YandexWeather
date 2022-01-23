# Contributing 

Everybody is invited and welcome to contribute.

## I have an idea or found a bug
Please, [open a new](https://github.com/IATkachenko/HA-YandexWeather/issues/new/choose) issue or subscribe to [existing](https://github.com/IATkachenko/HA-YandexWeather/issues).

## I want to improve something
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

Create [Pull Request](https://github.com/IATkachenko/HA-YandexWeather/compare) with description of motivation and improvements of your changes. 
This repository is using:
1. [black](https://github.com/psf/black) codestyle
2. [pre-commit](https://pre-commit.com/) for pre-checks
   ```commandline
   pip install -r requirements_test_pre_commit.txt
   pre-commit run --all-files
   ```
3. [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) 
4. CI/CD practices
   * make sure that your commits pass all existing tests
    ```commandline
   pip install -r requirements_test.txt
   pytest
    ```
   * make sure that all new code is covered by tests
5. Squash or rebase merging